from contextvars import ContextVar

from starlette.requests import Request

from pycraftcore.context.request_id_context import request_id_context

request_context: ContextVar[Request | None] = ContextVar("request", default=None)

__all__ = ["request_context", "request_id_context"]
