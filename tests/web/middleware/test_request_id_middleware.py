from typing import Any

import pytest

from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.web.middleware.request_id_middleware import RequestIDMiddleware


def http_scope(headers: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }


async def receive() -> dict[str, Any]:
    return {"type": "http.request", "body": b"", "more_body": False}


class RecordingSend:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def __call__(self, message: dict[str, Any]) -> None:
        self.messages.append(message)

    def header(self, name: bytes) -> list[bytes]:
        start = next(m for m in self.messages if m["type"] == "http.response.start")
        return [value for key, value in start["headers"] if key == name]


def responding_app(seen: dict[str, Any], headers: list[tuple[bytes, bytes]] | None = None):
    async def app(scope, receive, send) -> None:
        seen["request_id"] = request_id_context.get()
        await send({"type": "http.response.start", "status": 200, "headers": headers or []})
        await send({"type": "http.response.body", "body": b"ok"})

    return app


@pytest.mark.asyncio
async def test_uses_incoming_request_id_header_when_present():
    seen: dict[str, Any] = {}
    send = RecordingSend()

    await RequestIDMiddleware(responding_app(seen))(
        http_scope({"X-Request-ID": "incoming-id"}), receive, send
    )

    assert send.header(b"x-request-id") == [b"incoming-id"]
    assert seen["request_id"] == "incoming-id"
    assert request_id_context.get() is None


@pytest.mark.asyncio
async def test_generates_request_id_when_header_missing():
    seen: dict[str, Any] = {}
    send = RecordingSend()

    await RequestIDMiddleware(responding_app(seen))(http_scope(), receive, send)

    [generated] = send.header(b"x-request-id")
    assert len(generated) == 32
    assert seen["request_id"] == generated.decode()
    assert request_id_context.get() is None


@pytest.mark.asyncio
async def test_replaces_a_request_id_header_set_downstream():
    send = RecordingSend()
    app = responding_app({}, headers=[(b"X-Request-ID", b"other"), (b"content-type", b"x")])

    await RequestIDMiddleware(app)(http_scope({"X-Request-ID": "incoming-id"}), receive, send)

    assert send.header(b"x-request-id") == [b"incoming-id"]
    assert send.header(b"content-type") == [b"x"]


@pytest.mark.asyncio
async def test_request_id_context_is_reset_even_when_downstream_raises():
    async def failing_app(scope, receive, send) -> None:
        raise RuntimeError("downstream failure")

    with pytest.raises(RuntimeError, match="downstream failure"):
        await RequestIDMiddleware(failing_app)(
            http_scope({"X-Request-ID": "incoming-id"}), receive, RecordingSend()
        )

    assert request_id_context.get() is None


@pytest.mark.asyncio
async def test_non_http_scopes_pass_through_untouched():
    seen: dict[str, Any] = {}

    async def lifespan_app(scope, receive, send) -> None:
        seen["scope"] = scope
        seen["request_id"] = request_id_context.get()

    scope = {"type": "lifespan"}
    await RequestIDMiddleware(lifespan_app)(scope, receive, RecordingSend())

    assert seen == {"scope": scope, "request_id": None}


def test_generate_request_id_returns_a_hex_uuid():
    request_id = RequestIDMiddleware._generate_request_id()

    assert len(request_id) == 32
    int(request_id, 16)
