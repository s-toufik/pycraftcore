from contextvars import ContextVar
from typing import Optional

from starlette.requests import Request

request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
request_context: ContextVar[Request | None] = ContextVar("request", default=None)
