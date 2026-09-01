from unittest.mock import AsyncMock, MagicMock

import pytest

from pycraftcore.http.context.request_context import request_id_context
from pycraftcore.http.middleware.request_id_middleware import RequestIDMiddleware


def make_middleware() -> RequestIDMiddleware:
    return RequestIDMiddleware(app=MagicMock())


def make_request(headers: dict[str, str]) -> MagicMock:
    request = MagicMock()
    request.headers = headers
    return request


@pytest.mark.asyncio
async def test_uses_incoming_request_id_header_when_present():
    middleware = make_middleware()
    request = make_request({"X-Request-ID": "incoming-id"})
    response = MagicMock()
    response.headers = {}
    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)

    assert result.headers["X-Request-ID"] == "incoming-id"
    assert request_id_context.get() is None


@pytest.mark.asyncio
async def test_generates_request_id_when_header_missing():
    middleware = make_middleware()
    request = make_request({})
    response = MagicMock()
    response.headers = {}
    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)

    assert result.headers["X-Request-ID"]
    assert request_id_context.get() is None


@pytest.mark.asyncio
async def test_request_id_context_is_set_during_downstream_call():
    middleware = make_middleware()
    request = make_request({"X-Request-ID": "incoming-id"})
    response = MagicMock()
    response.headers = {}

    async def call_next(_request):
        assert request_id_context.get() == "incoming-id"
        return response

    await middleware.dispatch(request, call_next)


@pytest.mark.asyncio
async def test_request_id_context_is_reset_even_when_downstream_raises():
    middleware = make_middleware()
    request = make_request({"X-Request-ID": "incoming-id"})

    async def call_next(_request):
        raise RuntimeError("downstream failure")

    with pytest.raises(RuntimeError, match="downstream failure"):
        await middleware.dispatch(request, call_next)

    assert request_id_context.get() is None


@pytest.mark.asyncio
async def test_calls_downstream_handler_with_the_request():
    middleware = make_middleware()
    request = make_request({})
    response = MagicMock()
    response.headers = {}
    call_next = AsyncMock(return_value=response)

    await middleware.dispatch(request, call_next)

    call_next.assert_awaited_once_with(request)


def test_generate_request_id_returns_a_hex_uuid():
    request_id = RequestIDMiddleware._generate_request_id()

    assert len(request_id) == 32
    int(request_id, 16)
