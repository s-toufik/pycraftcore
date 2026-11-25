import json
from collections.abc import Iterable

from pycraftcore.jwt.exception.invalid_token_exception import InvalidTokenException
from pycraftcore.jwt.port.token_verifier import TokenVerifier
from pycraftcore.jwt.schema.token_claims import TokenClaims
from pycraftcore.web.asgi import ASGIApp, Receive, Scope, Send

_AUTHORIZATION: bytes = b"authorization"
_SCHEME: str = "bearer "


class BearerTokenMiddleware:
    def __init__(self, app: ASGIApp, verifier: TokenVerifier, protected: Iterable[str]) -> None:
        self.app = app
        self._verifier = verifier
        self._protected: tuple[str, ...] = tuple(path.rstrip("/") for path in protected)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self._protects(scope["path"]):
            await self.app(scope, receive, send)
            return

        token: str | None = self._bearer_token(scope)
        if token is None:
            await self._refuse(send, "a bearer token is required")
            return
        try:
            claims: TokenClaims = self._verifier.verify(token)
        except InvalidTokenException as error:
            await self._refuse(send, str(error))
            return

        scope.setdefault("state", {})["token_claims"] = claims
        await self.app(scope, receive, send)

    def _protects(self, path: str) -> bool:
        return any(path == prefix or path.startswith(f"{prefix}/") for prefix in self._protected)

    @staticmethod
    def _bearer_token(scope: Scope) -> str | None:
        for name, value in scope.get("headers", []):
            if name.lower() == _AUTHORIZATION:
                header: str = value.decode("latin-1")
                if header.lower().startswith(_SCHEME) and header[len(_SCHEME) :].strip():
                    return header[len(_SCHEME) :].strip()
        return None

    @staticmethod
    async def _refuse(send: Send, detail: str) -> None:
        body: bytes = json.dumps({"detail": detail}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"www-authenticate", b'Bearer error="invalid_token"'),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
