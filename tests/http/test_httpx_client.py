from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pycraftcore.http.adapter.httpx_client import HttpxClient, HttpxClientFactory
from pycraftcore.http.configuration import ClientSettings, HttpClientSettings
from pycraftcore.http.enum import HttpMethod


@pytest.mark.asyncio
async def test_create_client_returns_httpx_client_wrapping_instance():
    factory = HttpxClientFactory()

    client = factory.create_client()

    assert isinstance(client, HttpxClient)

    await factory.close()


@pytest.mark.asyncio
async def test_client_instance_uses_configured_limits_and_base_url():
    settings = HttpClientSettings(client_params=ClientSettings(base_url="https://api.test.com"))
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


@pytest.mark.asyncio
async def test_start_is_idempotent_and_reuses_the_same_client():
    factory = HttpxClientFactory()

    await factory.start()
    first = factory._client_instance
    await factory.start()
    second = factory._client_instance

    assert first is second

    await factory.close()


@pytest.mark.asyncio
async def test_factory_can_be_restarted_after_close():
    # Regression test: close() must evict the cached client so a later start()
    # builds a fresh one instead of handing back an already-closed AsyncClient.
    factory = HttpxClientFactory()

    await factory.start()
    first_client = factory._client_instance
    await factory.close()

    await factory.start()
    second_client = factory._client_instance

    assert second_client is not first_client
    assert second_client.is_closed is False

    await factory.close()


@pytest.mark.asyncio
async def test_create_client_after_restart_is_usable():
    calls = {"n": 0}

    async def handler(request):
        calls["n"] += 1
        return httpx.Response(200, json={"ok": True})

    settings = HttpClientSettings(client_params=ClientSettings(base_url="https://api.test.com"))
    factory = HttpxClientFactory(
        http_client_settings=settings, http_transport=httpx.MockTransport(handler)
    )

    await factory.start()
    await factory.close()
    await factory.start()

    client = factory.create_client()
    result = await client.get("/health")

    assert result == {"ok": True}
    assert calls["n"] == 1

    await factory.close()


@pytest.mark.asyncio
async def test_context_manager_starts_and_closes():
    async with HttpxClientFactory() as factory:
        client = factory.create_client()
        assert isinstance(client, HttpxClient)
        underlying = factory._client_instance

    assert underlying.is_closed is True
    # Accessing the cached_property again after close must not resurrect the
    # closed client: close() evicts the cache so this rebuilds a fresh one.
    assert "_client_instance" not in factory.__dict__


def test_create_ssl_from_certificate_returns_true_without_certificate():
    # `True` tells httpx to use the default (verifying) SSL context.
    factory = HttpxClientFactory()

    assert factory._create_ssl_from_certificate() is True


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


def test_transport_defaults_to_a_working_http_transport_with_no_retries():
    # retries=0 because tenacity owns retry policy at the resilient-client layer;
    # the raw transport must not silently retry underneath it.
    factory = HttpxClientFactory()

    transport = factory._transport()

    assert isinstance(transport, httpx.AsyncHTTPTransport)


def test_transport_reuses_an_externally_provided_transport():
    external_transport = MagicMock(spec=httpx.AsyncBaseTransport)
    factory = HttpxClientFactory(http_transport=external_transport)

    assert factory._transport() is external_transport


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
async def test_event_log_does_nothing_without_logger():
    factory = HttpxClientFactory()
    request = MagicMock()

    await factory._event_log(request)  # must not raise

    await factory.close()


def test_event_hooks_registers_request_logger():
    factory = HttpxClientFactory()

    hooks = factory._event_hooks()

    assert hooks == {"request": [factory._event_log]}


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


@pytest.mark.asyncio
async def test_get_delegates_with_expected_method_and_params():
    inner_client = AsyncMock()
    response = MagicMock()
    response.headers = {"content-type": "application/json"}
    response.content = b"{}"
    inner_client.request = AsyncMock(return_value=response)

    client = HttpxClient(inner_client)

    await client.get("/health", params={"q": "1"}, headers={"X-A": "b"})

    inner_client.request.assert_awaited_once_with(
        method=HttpMethod.GET.value,
        url="/health",
        params={"q": "1"},
        json=None,
        headers={"X-A": "b"},
    )


@pytest.mark.asyncio
async def test_post_delegates_with_expected_method_and_body():
    inner_client = AsyncMock()
    response = MagicMock()
    response.headers = {"content-type": "application/json"}
    response.content = b"{}"
    inner_client.request = AsyncMock(return_value=response)

    client = HttpxClient(inner_client)

    await client.post("/users", body={"name": "john"})

    inner_client.request.assert_awaited_once_with(
        method=HttpMethod.POST.value,
        url="/users",
        params=None,
        json={"name": "john"},
        headers=None,
    )
