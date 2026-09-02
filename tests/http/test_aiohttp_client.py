from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import orjson
import pytest

from pycraftcore.http.adapter import AioHttpClient, AioHttpClientFactory
from pycraftcore.http.configuration import HttpClientSettings
from pycraftcore.http.enum import HttpMethod
from pycraftcore.http.port import AsyncHttpClient


def test_build_url_normalization():
    client = AioHttpClient(base_url="https://api.test.com/", session=MagicMock())

    assert client._build_url("/users") == "https://api.test.com/users"
    assert client._build_url("users") == "https://api.test.com/users"


def test_build_url_without_base_url():
    # With no base_url, aiohttp needs an absolute URL: the endpoint passes through untouched.
    client = AioHttpClient(base_url="", session=MagicMock())

    assert client._build_url("/users") == "/users"
    assert client._build_url("https://api.test.com/users") == "https://api.test.com/users"


@pytest.mark.asyncio
async def test_factory_ensure_session_raises_without_start():
    factory = AioHttpClientFactory()

    with pytest.raises(RuntimeError, match="Factory session is not started"):
        factory.create_client()


@pytest.mark.asyncio
async def test_factory_start_creates_session_and_client():
    factory = AioHttpClientFactory()

    await factory.start()
    client = factory.create_client()

    assert isinstance(client, AioHttpClient)
    assert isinstance(factory._session, aiohttp.ClientSession)

    await factory.close()


@pytest.mark.asyncio
async def test_factory_start_is_idempotent_and_reuses_the_same_session():
    factory = AioHttpClientFactory()

    await factory.start()
    first_session = factory._session
    await factory.start()
    second_session = factory._session

    assert first_session is second_session

    await factory.close()


@pytest.mark.asyncio
async def test_factory_close_closes_owned_session():
    factory = AioHttpClientFactory()

    await factory.start()
    session = factory._session

    await factory.close()

    assert factory._session is None
    assert session.closed is True


@pytest.mark.asyncio
async def test_factory_close_does_not_close_external_connector():
    # A bare AsyncMock() would make every auto-generated child attribute (e.g. `._loop`,
    # which aiohttp.ClientSession reads synchronously) an AsyncMock too, so calling it
    # produces an unawaited coroutine. MagicMock keeps children sync by default; only
    # `.close` needs to be async here.
    external_connector = MagicMock()
    external_connector.closed = False
    external_connector.close = AsyncMock()

    factory = AioHttpClientFactory(connector=external_connector)

    await factory.start()
    await factory.close()

    external_connector.close.assert_not_called()
    assert factory._connector is external_connector


@pytest.mark.asyncio
async def test_factory_close_closes_owned_connector():
    factory = AioHttpClientFactory()

    await factory.start()
    connector = factory._connector

    await factory.close()

    assert connector.closed is True
    assert factory._connector is None


@pytest.mark.asyncio
async def test_factory_can_be_restarted_after_close():
    factory = AioHttpClientFactory()

    await factory.start()
    first_session = factory._session
    await factory.close()

    await factory.start()
    second_session = factory._session

    assert second_session is not None
    assert second_session is not first_session
    assert second_session.closed is False

    await factory.close()


@pytest.mark.asyncio
async def test_factory_context_manager_starts_and_closes():
    async with AioHttpClientFactory() as factory:
        client = factory.create_client()
        assert isinstance(client, AioHttpClient)

    assert factory._session is None


def test_factory_create_ssl_from_certificate_defaults_to_verified_ssl_without_certificate():
    # `True` tells aiohttp to use the default (verifying) SSL context; `False` would
    # disable certificate verification entirely, so the secure default must be True.
    factory = AioHttpClientFactory()

    assert factory._create_ssl_from_certificate() is True


def test_factory_create_ssl_from_certificate_builds_context(tmp_path):
    cert_path = tmp_path / "cert.pem"
    cert_path.write_text("fake")
    settings = HttpClientSettings()
    settings.security.certificate = str(cert_path)
    settings.security.tls_cipher_spec = "TLS_AES_256_GCM_SHA384"
    factory = AioHttpClientFactory(http_client_settings=settings)

    with patch("ssl.create_default_context") as mock_ctx_factory:
        mock_ctx = MagicMock()
        mock_ctx_factory.return_value = mock_ctx

        result = factory._create_ssl_from_certificate()

        mock_ctx.load_verify_locations.assert_called_once_with(cafile=str(cert_path))
        mock_ctx.set_ciphers.assert_called_once_with("TLS_AES_256_GCM_SHA384")
        assert result is mock_ctx


@pytest.mark.asyncio
async def test_request_json_response():
    session = MagicMock()
    client = AioHttpClient(base_url="https://api.test.com", session=session)

    mock_response = AsyncMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.read = AsyncMock(return_value=orjson.dumps({"ok": True}))
    mock_response.raise_for_status = MagicMock()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response

    session.request = MagicMock(return_value=mock_ctx)

    result = await client._request("GET", "/health")
    assert result == {"ok": True}
    result = await client.get(endpoint="/health")
    assert result == {"ok": True}
    result = await client.post(endpoint="/health")
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_request_text_response():
    session = MagicMock()
    client = AioHttpClient(base_url="https://api.test.com", session=session)

    mock_response = AsyncMock()
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.text = AsyncMock(return_value="healthy")
    mock_response.raise_for_status = MagicMock()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response

    session.request = MagicMock(return_value=mock_ctx)

    result = await client._request("GET", "/health")
    assert result == "healthy"
    result = await client.get("/health")
    assert result == "healthy"
    result = await client.post("/health")
    assert result == "healthy"


@pytest.mark.asyncio
async def test_http_client_protocol():
    class MockHttpClient(AsyncHttpClient):
        async def start(self) -> None:
            pass

        async def close(self) -> None:
            pass

        async def get(self, endpoint: str, *, params=None, headers=None) -> Any:
            return {"ok": True}

        async def post(self, endpoint: str, *, body=None, headers=None) -> Any:
            return {"ok": True}

    client = MockHttpClient()
    await client.start()

    result = await client.get(endpoint="/health")
    assert result == {"ok": True}
    result = await client.post(endpoint="/health")
    assert result == {"ok": True}

    await client.close()


def test_slots_prevents_dynamic_attributes():
    client = AioHttpClient(base_url="https://api.test.com", session=MagicMock())

    with pytest.raises(AttributeError):
        client.new_attribute = "fail"


@pytest.mark.asyncio
async def test_post_delegation():
    client = AioHttpClient(base_url="https://api.test.com", session=MagicMock())
    mock_request = AsyncMock(return_value={"created": True})

    with patch.object(AioHttpClient, "_request", mock_request):
        result = await client.post("/users", body={"name": "john"})

    assert result == {"created": True}

    mock_request.assert_awaited_once_with(
        HttpMethod.POST.value,
        "/users",
        json={"name": "john"},
        headers=None,
    )
