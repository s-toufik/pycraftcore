from typing import Any

import aiohttp
import pytest
import orjson

from unittest.mock import AsyncMock, MagicMock

from pycraftcore.http.adapter import AioHttpClient
from pycraftcore.http.enum import HttpMethod
from pycraftcore.http.port import AsyncHttpClient


def test_build_url_normalization():
    client = AioHttpClient(base_url="https://api.test.com/")

    assert client._build_url("/users") == "https://api.test.com/users"
    assert client._build_url("users") == "https://api.test.com/users"


def test_ensure_session_raises_without_start():
    client = AioHttpClient(base_url="https://api.test.com")

    with pytest.raises(RuntimeError, match="Client session is not started"):
        client._ensure_session()


@pytest.mark.asyncio
async def test_start_creates_session():
    client = AioHttpClient(base_url="https://api.test.com")

    await client.start()

    assert isinstance(client._ensure_session(), aiohttp.ClientSession)

    await client.close()


@pytest.mark.asyncio
async def test_close_closes_owned_session():
    client = AioHttpClient(base_url="https://api.test.com")

    await client.start()
    session = client._ensure_session()

    await client.close()

    assert client._session is None
    assert session.closed is True


@pytest.mark.asyncio
async def test_close_does_not_close_external_session():
    external_session = AsyncMock()
    external_session.closed = False
    external_session.close = AsyncMock()

    client = AioHttpClient(
        base_url="https://api.test.com",
        session=external_session,
    )

    await client.close()

    external_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_close_does_not_close_external_connector():
    external_connector = AsyncMock()
    external_connector.closed = False
    external_connector.close = AsyncMock()

    client = AioHttpClient(
        base_url="https://api.test.com",
        connector=external_connector,
    )

    await client.close()

    external_connector.close.assert_not_called()


@pytest.mark.asyncio
async def test_request_json_response():
    client = AioHttpClient(base_url="https://api.test.com")
    await client.start()

    mock_response = AsyncMock()
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.read = AsyncMock(return_value=orjson.dumps({"ok": True}))
    mock_response.raise_for_status = MagicMock()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response

    client._session.request = MagicMock(return_value=mock_ctx)

    result = await client._request("GET", "/health")
    assert result == {"ok": True}
    result = await client.get(endpoint="/health")
    assert result == {"ok": True}
    result = await client.post(endpoint="/health")
    assert result == {"ok": True}

    await client.close()


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


@pytest.mark.asyncio
async def test_request_text_response():
    client = AioHttpClient(base_url="https://api.test.com")
    await client.start()

    mock_response = AsyncMock()
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.text = AsyncMock(return_value="healthy")
    mock_response.raise_for_status = MagicMock()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response

    client._session.request = MagicMock(return_value=mock_ctx)

    result = await client._request("GET", "/health")
    assert result == "healthy"
    result = await client.get("/health")
    assert result == "healthy"
    result = await client.post("/health")
    assert result == "healthy"

    await client.close()


def test_slots_prevents_dynamic_attributes():
    client = AioHttpClient(base_url="https://api.test.com")

    with pytest.raises(AttributeError):
        client.new_attribute = "fail"  # noqa


@pytest.mark.asyncio
async def test_post_delegation():
    client = AioHttpClient(base_url="https://api.test.com")
    mock_request = AsyncMock(return_value={"created": True})
    AioHttpClient._request = mock_request

    result = await client.post("/users", body={"name": "john"})
    assert result == {"created": True}

    mock_request.assert_awaited_once_with(
        HttpMethod.POST.value,
        "/users",
        json={"name": "john"},
        headers=None,
    )
