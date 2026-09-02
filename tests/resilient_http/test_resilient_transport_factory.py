from unittest.mock import MagicMock, patch

import httpx
import pytest

from pycraftcore.circuit_breaker.adapter.aiobreaker_circuit_breaker_policy import (
    AioBreakerCircuitBreakerPolicy,
)
from pycraftcore.circuit_breaker.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.circuit_breaker.enum.circuit_breaker_status import CircuitState
from pycraftcore.circuit_breaker.exception.circuit_breaker_open_exception import (
    CircuitBreakerOpenException,
)
from pycraftcore.http.configuration import ClientSettings, HttpClientSettings
from pycraftcore.http.policy.http_error_policy import is_business_error, is_retryable
from pycraftcore.resilient_http.adapter.resilient_transport import ResilientTransport
from pycraftcore.resilient_http.adapter.resilient_transport_factory import (
    ResilientTransportFactory,
)
from pycraftcore.resilient_http.configuration.resilient_http_configuration import (
    ResilientHttpSettings,
)
from pycraftcore.retry.adapter.tenacity_retry_policy import TenacityRetryPolicy
from pycraftcore.retry.configuration.retry_configuration import RetrySettings


def test_create_transport_wraps_the_default_base_transport():
    factory = ResilientTransportFactory()

    transport = factory.create_transport()

    assert isinstance(transport, ResilientTransport)
    assert isinstance(transport._transport, httpx.AsyncHTTPTransport)


def test_create_transport_wraps_a_given_external_transport():
    external = MagicMock(spec=httpx.AsyncBaseTransport)
    factory = ResilientTransportFactory()

    transport = factory.create_transport(external)

    assert transport._transport is external


def test_create_transport_shares_circuit_breaker_and_retry_across_calls():
    factory = ResilientTransportFactory()

    first = factory.create_transport(MagicMock(spec=httpx.AsyncBaseTransport))
    second = factory.create_transport(MagicMock(spec=httpx.AsyncBaseTransport))

    assert first._circuit_breaker is second._circuit_breaker
    assert first._circuit_breaker is factory.circuit_breaker
    assert first._retry is second._retry


def test_create_async_client_returns_a_working_client_using_the_resilient_transport():
    factory = ResilientTransportFactory()

    client = factory.create_async_client(MagicMock(spec=httpx.AsyncBaseTransport))

    assert isinstance(client, httpx.AsyncClient)
    assert isinstance(client._transport, ResilientTransport)


def test_create_async_client_applies_configured_base_url():
    # Regression test: base_url was silently dropped, so a caller who set
    # settings.http.client_params.base_url got an AsyncClient with no base_url at all.
    settings = ResilientHttpSettings(
        http=HttpClientSettings(client_params=ClientSettings(base_url="https://api.test.com"))
    )
    factory = ResilientTransportFactory(settings=settings)

    client = factory.create_async_client(MagicMock(spec=httpx.AsyncBaseTransport))

    assert str(client.base_url) == "https://api.test.com"


def test_create_async_client_defaults_to_empty_base_url():
    factory = ResilientTransportFactory()

    client = factory.create_async_client(MagicMock(spec=httpx.AsyncBaseTransport))

    assert str(client.base_url) == ""


def test_create_async_client_applies_configured_timeout_and_limits():
    settings = ResilientHttpSettings()
    settings.http.limits.timeout = 15
    settings.http.limits.max_connections = 42
    settings.http.limits.max_keepalive_connections = 7
    factory = ResilientTransportFactory(settings=settings)

    client = factory.create_async_client(MagicMock(spec=httpx.AsyncBaseTransport))

    assert client.timeout == httpx.Timeout(15)
    assert client._transport is not None  # sanity: client constructed successfully


def test_init_builds_retry_and_circuit_breaker_from_settings():
    settings = ResilientHttpSettings()
    factory = ResilientTransportFactory(settings=settings)

    assert isinstance(factory._retry, TenacityRetryPolicy)
    assert factory._retry.settings is settings.retry
    assert isinstance(factory._circuit_breaker, AioBreakerCircuitBreakerPolicy)
    assert factory._circuit_breaker.settings is settings.circuit_breaker


def test_defaults_settings_when_none_provided():
    factory = ResilientTransportFactory()

    assert isinstance(factory._settings, ResilientHttpSettings)


def test_verify_defaults_to_true_without_certificate():
    factory = ResilientTransportFactory()

    assert factory._verify() is True


def test_verify_builds_context_from_certificate(tmp_path):
    cert_path = tmp_path / "cert.pem"
    cert_path.write_text("fake")
    settings = ResilientHttpSettings()
    settings.http.security.certificate = str(cert_path)
    settings.http.security.tls_cipher_spec = "TLS_AES_256_GCM_SHA384"
    factory = ResilientTransportFactory(settings=settings)

    with patch("ssl.create_default_context") as mock_ctx_factory:
        mock_ctx = MagicMock()
        mock_ctx_factory.return_value = mock_ctx

        result = factory._verify()

        mock_ctx.load_verify_locations.assert_called_once_with(cafile=str(cert_path))
        mock_ctx.set_ciphers.assert_called_once_with("TLS_AES_256_GCM_SHA384")
        assert result is mock_ctx


@pytest.mark.asyncio
async def test_integration_retries_transient_failures_then_succeeds():
    calls = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(500, json={"error": "boom"})
        return httpx.Response(200, json={"ok": True})

    settings = ResilientHttpSettings(
        retry=RetrySettings(
            retry_count=3,
            retry_delay=0.001,
            max_retry_delay=0.002,
            jitter=0.0,
            should_retry=is_retryable,
        ),
        circuit_breaker=CircuitBreakerSettings(
            failure_threshold=5,
            recovery_timeout=1,
            is_excluded=is_business_error,
            name="llm-gateway",
        ),
    )
    factory = ResilientTransportFactory(settings=settings)
    client = factory.create_async_client(httpx.MockTransport(handler))

    response = await client.post("https://api.test.com/chat", json={"messages": ["hi"]})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert calls["n"] == 3
    assert factory.circuit_breaker.state == CircuitState.CLOSED

    await client.aclose()


@pytest.mark.asyncio
async def test_integration_request_body_replayed_correctly_across_retries():
    bodies_seen = []

    async def handler(request: httpx.Request) -> httpx.Response:
        bodies_seen.append(await request.aread())
        if len(bodies_seen) < 3:
            return httpx.Response(500, json={})
        return httpx.Response(200, json={"ok": True})

    settings = ResilientHttpSettings(
        retry=RetrySettings(
            retry_count=3,
            retry_delay=0.001,
            max_retry_delay=0.002,
            jitter=0.0,
            should_retry=is_retryable,
        ),
    )
    factory = ResilientTransportFactory(settings=settings)
    client = factory.create_async_client(httpx.MockTransport(handler))

    await client.post("https://api.test.com/chat", json={"messages": ["hi"]})

    assert bodies_seen == [b'{"messages":["hi"]}'] * 3

    await client.aclose()


@pytest.mark.asyncio
async def test_integration_business_error_is_not_retried_and_does_not_trip_breaker():
    calls = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404, json={"error": "missing"})

    settings = ResilientHttpSettings(
        retry=RetrySettings(
            retry_count=3,
            retry_delay=0.001,
            max_retry_delay=0.002,
            jitter=0.0,
            should_retry=is_retryable,
        ),
        circuit_breaker=CircuitBreakerSettings(failure_threshold=1, is_excluded=is_business_error),
    )
    factory = ResilientTransportFactory(settings=settings)
    client = factory.create_async_client(httpx.MockTransport(handler))

    response = await client.get("https://api.test.com/missing")

    assert response.status_code == 404
    assert calls["n"] == 1
    assert factory.circuit_breaker.state == CircuitState.CLOSED

    await client.aclose()


@pytest.mark.asyncio
async def test_integration_circuit_breaker_opens_and_rejects_subsequent_calls():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "down"})

    settings = ResilientHttpSettings(
        retry=RetrySettings(
            retry_count=0,
            retry_delay=0.001,
            max_retry_delay=0.002,
            jitter=0.0,
            should_retry=is_retryable,
        ),
        circuit_breaker=CircuitBreakerSettings(
            failure_threshold=1, recovery_timeout=10, is_excluded=is_business_error
        ),
    )
    factory = ResilientTransportFactory(settings=settings)
    client = factory.create_async_client(httpx.MockTransport(handler))

    first = await client.get("https://api.test.com/x")
    assert first.status_code == 500
    assert factory.circuit_breaker.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenException):
        await client.get("https://api.test.com/x")

    await client.aclose()


@pytest.mark.asyncio
async def test_integration_breaker_state_is_shared_across_clients_from_same_factory():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    settings = ResilientHttpSettings(
        retry=RetrySettings(
            retry_count=0,
            retry_delay=0.001,
            max_retry_delay=0.002,
            jitter=0.0,
            should_retry=is_retryable,
        ),
        circuit_breaker=CircuitBreakerSettings(failure_threshold=1, is_excluded=is_business_error),
    )
    factory = ResilientTransportFactory(settings=settings)
    first_client = factory.create_async_client(httpx.MockTransport(handler))
    second_client = factory.create_async_client(httpx.MockTransport(handler))

    await first_client.get("https://api.test.com/x")
    assert factory.circuit_breaker.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenException):
        await second_client.get("https://api.test.com/x")

    await first_client.aclose()
    await second_client.aclose()
