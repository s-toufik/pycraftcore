import uuid
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from pycraftcore.http.context.request_context import request_id_context


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:

        request_id = request.headers.get("X-Request-ID") or self._generate_request_id()
        request_id_context.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

    @staticmethod
    def _generate_request_id() -> str:
        return uuid.uuid4().hex
