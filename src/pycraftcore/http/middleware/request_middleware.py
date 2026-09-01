from collections.abc import Awaitable, Callable
from contextvars import Token

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from pycraftcore.http.context.request_context import request_context


class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        token: Token = request_context.set(request)
        try:
            response: Response = await call_next(request)
        finally:
            request_context.reset(token)

        return response
