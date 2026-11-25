import json
from datetime import timedelta
from typing import Any

import pytest

from pycraftcore.jwt.adapter import PyJwtTokens
from pycraftcore.web.middleware import BearerTokenMiddleware

pytestmark = pytest.mark.asyncio

TOKENS = PyJwtTokens("k" * 32)
VALID = TOKENS.issue("toufik", timedelta(hours=5))


def http_scope(path: str, authorization: str | None = None) -> dict[str, Any]:
    headers = [(b"authorization", authorization.encode())] if authorization is not None else []
    return {"type": "http", "path": path, "headers": headers}


async def receive() -> dict[str, Any]:
    return {"type": "http.request", "body": b"", "more_body": False}


class RecordingSend:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def __call__(self, message: dict[str, Any]) -> None:
        self.messages.append(message)

    @property
    def status(self) -> int:
        return next(m for m in self.messages if m["type"] == "http.response.start")["status"]

    @property
    def body(self) -> dict[str, Any]:
        return json.loads(
            next(m for m in self.messages if m["type"] == "http.response.body")["body"]
        )


async def call(path: str, authorization: str | None = None) -> tuple[RecordingSend, dict]:
    seen: dict[str, Any] = {}

    async def app(scope, receive, send) -> None:
        seen["claims"] = scope.get("state", {}).get("token_claims")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    send = RecordingSend()
    await BearerTokenMiddleware(app, TOKENS, protected=["/mcp/"])(
        http_scope(path, authorization), receive, send
    )
    return send, seen


@pytest.mark.parametrize("path", ["/mcp", "/mcp/kitchen"])
async def test_a_valid_bearer_token_reaches_a_protected_path_with_its_claims(path) -> None:
    send, seen = await call(path, f"Bearer {VALID}")

    assert send.status == 200
    assert seen["claims"].subject == "toufik"


@pytest.mark.parametrize(
    ("authorization", "detail"),
    [
        (None, "a bearer token is required"),
        ("Basic dXNlcjpwYXNz", "a bearer token is required"),
        ("Bearer ", "a bearer token is required"),
        ("Bearer not.a.token", "the token is not valid"),
    ],
)
async def test_a_protected_path_refuses_a_missing_or_invalid_token(authorization, detail) -> None:
    send, seen = await call("/mcp/kitchen", authorization)

    assert send.status == 401
    assert send.body["detail"].startswith(detail)
    start = send.messages[0]
    assert (b"www-authenticate", b'Bearer error="invalid_token"') in start["headers"]
    assert seen == {}


@pytest.mark.parametrize("path", ["/actuator/health", "/auth/token", "/mcpx"])
async def test_other_paths_pass_without_a_token(path) -> None:
    send, seen = await call(path)

    assert send.status == 200
    assert seen["claims"] is None


async def test_the_scheme_is_case_insensitive() -> None:
    send, _ = await call("/mcp", f"bearer {VALID}")

    assert send.status == 200
