from contextvars import ContextVar

from starlette.requests import Request

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
request_context: ContextVar[Request | None] = ContextVar("request", default=None)
