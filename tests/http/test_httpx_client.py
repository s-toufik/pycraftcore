from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pycraftcore.http.adapter.httpx_client import (
    BreakerLogger,
    HttpxClient,
    HttpxClientFactory,
    ResilientTransport,
)
from pycraftcore.http.configuration import HttpClientSettings


@pytest.mark.asyncio
async def test_create_client_returns_httpx_client_wrapping_instance():
    factory = HttpxClientFactory()

    client = factory.create_client()

    assert isinstance(client, HttpxClient)

    await factory.close()


@pytest.mark.asyncio
async def test_client_instance_uses_configured_limits_and_base_url():
    settings = HttpClientSettings()
    settings.client_params.base_url = "https://api.test.com"
    factory = HttpxClientFactory(http_client_settings=settings)

    instance = factory._client_instance

    assert str(instance.base_url) == "https://api.test.com"

    await factory.close()


@pytest.mark.asyncio
async def test_close_closes_the_client():
    factory = HttpxClientFactory()
    instance = factory._client_instance

    await factory.close()

    assert instance.is_closed is True


@pytest.mark.asyncio
async def test_close_is_idempotent():
    factory = HttpxClientFactory()
    _ = factory._client_instance

    await factory.close()
    await factory.close()


@pytest.mark.asyncio
async def test_close_does_not_instantiate_a_client_that_was_never_used():
    factory = HttpxClientFactory()

    await factory.close()

    assert "_client_instance" not in factory.__dict__
    assert "_resilient_client_instance" not in factory.__dict__


@pytest.mark.asyncio
async def test_close_closes_both_plain_and_resilient_client_when_both_are_used():
    factory = HttpxClientFactory()
    plain = factory._client_instance
    resilient = factory.resilient_client_instance

    await factory.close()

    assert plain.is_closed is True
    assert resilient.is_closed is True


@pytest.mark.asyncio
async def test_context_manager_starts_and_closes():
    async with HttpxClientFactory() as factory:
        client = factory.create_client()
        assert isinstance(client, HttpxClient)

    assert factory._client_instance.is_closed is True


def test_resilient_client_instance_uses_resilient_transport():
    factory = HttpxClientFactory()

    instance = factory.resilient_client_instance

    assert isinstance(instance._transport, ResilientTransport)


def test_create_ssl_from_certificate_returns_false_without_certificate():
    factory = HttpxClientFactory()

    assert factory._create_ssl_from_certificate() is False


def test_create_ssl_from_certificate_builds_context(tmp_path):
    cert_path = tmp_path / "cert.pem"
    cert_path.write_text(
        "-----BEGIN CERTIFICATE-----\nMIIBAjCB..fake..\n-----END CERTIFICATE-----\n"
    )
    settings = HttpClientSettings()
    settings.security.certificate = str(cert_path)
    factory = HttpxClientFactory(http_client_settings=settings)

    with patch("ssl.create_default_context") as mock_ctx_factory:
        mock_ctx = MagicMock()
        mock_ctx_factory.return_value = mock_ctx

        result = factory._create_ssl_from_certificate()

        mock_ctx.load_verify_locations.assert_called_once_with(cafile=str(cert_path))
        assert result is mock_ctx


def test_create_ssl_from_certificate_sets_cipher_spec_when_provided(tmp_path):
    cert_path = tmp_path / "cert.pem"
    cert_path.write_text("fake")
    settings = HttpClientSettings()
    settings.security.certificate = str(cert_path)
    settings.security.tls_cipher_spec = "TLS_AES_256_GCM_SHA384"
    factory = HttpxClientFactory(http_client_settings=settings)

    with patch("ssl.create_default_context") as mock_ctx_factory:
        mock_ctx = MagicMock()
        mock_ctx_factory.return_value = mock_ctx

        factory._create_ssl_from_certificate()

        mock_ctx.set_ciphers.assert_called_once_with("TLS_AES_256_GCM_SHA384")


@pytest.mark.asyncio
async def test_event_log_logs_request_when_logger_provided():
    logger = MagicMock()
    factory = HttpxClientFactory(logger=logger)
    request = MagicMock()
    request.method = "GET"
    request.url = "https://api.test.com/health"

    await factory._event_log(request)

    logger.info.assert_called_once_with("Request GET https://api.test.com/health")

    await factory.close()


@pytest.mark.asyncio
async def test_request_returns_json_when_content_type_is_json():
    inner_client = AsyncMock()
    response = MagicMock()
    response.headers = {"content-type": "application/json"}
    response.content = b'{"ok": true}'
    response.raise_for_status = MagicMock()
    inner_client.request = AsyncMock(return_value=response)

    client = HttpxClient(inner_client)

    result = await client.get("/health")

    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_request_returns_text_when_content_type_is_not_json():
    inner_client = AsyncMock()
    response = MagicMock()
    response.headers = {"content-type": "text/plain"}
    response.text = "healthy"
    response.raise_for_status = MagicMock()
    inner_client.request = AsyncMock(return_value=response)

    client = HttpxClient(inner_client)

    result = await client.post("/health", body={"a": 1})

    assert result == "healthy"


@pytest.mark.asyncio
async def test_request_returns_text_when_content_type_header_is_missing():
    inner_client = AsyncMock()
    response = MagicMock()
    response.headers = {}
    response.text = "healthy"
    response.raise_for_status = MagicMock()
    inner_client.request = AsyncMock(return_value=response)

    client = HttpxClient(inner_client)

    result = await client.get("/health")

    assert result == "healthy"


@pytest.mark.asyncio
async def test_request_raises_for_error_status():
    inner_client = AsyncMock()
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "error", request=MagicMock(), response=MagicMock()
    )
    inner_client.request = AsyncMock(return_value=response)

    client = HttpxClient(inner_client)

    with pytest.raises(httpx.HTTPStatusError):
        await client.get("/health")


class TestBreakerLogger:
    def test_failure_stores_exception_and_logs(self):
        logger = MagicMock()
        breaker_logger = BreakerLogger(logger)
        breaker = MagicMock(fail_counter=1, fail_max=3)
        exception = ValueError("boom")

        breaker_logger.failure(breaker, exception)

        assert breaker_logger._last_exception is exception
        logger.warning.assert_called_once()

    def test_success_clears_last_exception(self):
        breaker_logger = BreakerLogger()
        breaker_logger._last_exception = ValueError("boom")

        breaker_logger.success(MagicMock())

        assert breaker_logger._last_exception is None

    def test_state_change_logs_info(self):
        logger = MagicMock()
        breaker_logger = BreakerLogger(logger)
        old_state = MagicMock(name="CLOSED")
        old_state.name = "CLOSED"
        new_state = MagicMock(name="HALF_OPEN")
        new_state.name = "HALF_OPEN"

        breaker_logger.state_change(MagicMock(), old_state, new_state)

        logger.info.assert_called_once()
        logger.error.assert_not_called()

    def test_state_change_logs_error_when_opening(self):
        from aiobreaker import CircuitBreakerState

        logger = MagicMock()
        breaker_logger = BreakerLogger(logger)
        breaker = MagicMock(fail_counter=3, fail_max=3)
        breaker.timeout_duration.total_seconds.return_value = 30.0
        old_state = MagicMock(name="CLOSED")
        old_state.name = "CLOSED"

        breaker_logger.state_change(breaker, old_state, CircuitBreakerState.OPEN)

        logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_resilient_transport_delegates_through_breaker_and_retry():
    inner_transport = AsyncMock()
    response = MagicMock()
    inner_transport.handle_async_request = AsyncMock(return_value=response)

    settings = HttpClientSettings()
    transport = ResilientTransport(http_client_settings=settings, transport=inner_transport)

    request = MagicMock()
    result = await transport.handle_async_request(request)

    assert result is response
    inner_transport.handle_async_request.assert_awaited_once_with(request)


@pytest.mark.asyncio
async def test_resilient_transport_logs_and_retries_on_transient_failure():
    inner_transport = AsyncMock()
    response = MagicMock()
    inner_transport.handle_async_request = AsyncMock(
        side_effect=[httpx.TransportError("boom"), response]
    )
    logger = MagicMock()

    settings = HttpClientSettings()
    settings.retry.retry_count = 2
    settings.retry.retry_delay = 0.01
    settings.retry.retry_on = (httpx.TransportError,)

    transport = ResilientTransport(
        http_client_settings=settings, logger=logger, transport=inner_transport
    )

    result = await transport.handle_async_request(MagicMock())

    assert result is response
    assert inner_transport.handle_async_request.await_count == 2
    logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_resilient_transport_breaker_timeout_duration_is_in_seconds_not_days():
    settings = HttpClientSettings()
    settings.circuit_breaker.recovery_timeout = 30
    transport = ResilientTransport(http_client_settings=settings)

    try:
        assert transport._breaker.timeout_duration.total_seconds() == 30
    finally:
        await transport.aclose()


@pytest.mark.asyncio
async def test_resilient_transport_defaults_to_a_working_http_transport():
    settings = HttpClientSettings()
    transport = ResilientTransport(http_client_settings=settings)

    try:
        assert isinstance(transport._transport, httpx.AsyncHTTPTransport)
    finally:
        await transport.aclose()


@pytest.mark.asyncio
async def test_resilient_transport_aclose_closes_underlying_transport():
    inner_transport = AsyncMock()
    settings = HttpClientSettings()
    transport = ResilientTransport(http_client_settings=settings, transport=inner_transport)

    await transport.aclose()

    inner_transport.aclose.assert_awaited_once()
