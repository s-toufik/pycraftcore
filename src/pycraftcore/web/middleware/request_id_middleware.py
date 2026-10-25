import uuid
from contextvars import Token

from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.web.asgi import ASGIApp, Message, Receive, Scope, Send

_HEADER: bytes = b"x-request-id"


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id: str = self._incoming(scope) or self._generate_request_id()

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != _HEADER
                ]
                headers.append((_HEADER, request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        token: Token = request_id_context.set(request_id)
        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_context.reset(token)

    @staticmethod
    def _incoming(scope: Scope) -> str | None:
        for name, value in scope.get("headers", []):
            if name.lower() == _HEADER and value:
                return value.decode("latin-1")
        return None

    @staticmethod
    def _generate_request_id() -> str:
        return uuid.uuid4().hex
