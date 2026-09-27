from contextvars import ContextVar

# Kept free of any web framework so logging can read it without importing Starlette.
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
