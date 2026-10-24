import logging
import sys

from pycraftcore.context.request_id_context import request_id_context

LOG_FORMAT: str = (
    "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(request_id)s | "
    "%(module)s:%(funcName)s:%(lineno)d - %(message)s"
)
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
NO_REQUEST_ID: str = "-"

QUIET_LOGGERS: tuple[str, ...] = (
    "aiosqlite",
    "anthropic",
    "asyncio",
    "httpcore",
    "httpcore2",
    "httpx",
    "httpx2",
    "mcp",
    "openai",
    "pymongo",
    "urllib3",
)

SERVER_LOGGERS: tuple[str, ...] = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "_granian",
    "granian.access",
)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request_id = request_id_context.get()
        if request_id:
            record.request_id = request_id
        return True


class _ConsoleHandler(logging.StreamHandler): ...


def configure_logging(level: str | int = logging.INFO) -> None:
    handler = _ConsoleHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(LOG_FORMAT, DATE_FORMAT, defaults={"request_id": NO_REQUEST_ID})
    )
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    for existing in [h for h in root.handlers if isinstance(h, _ConsoleHandler)]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    quiet_level: int = max(logging.WARNING, root.level)
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(quiet_level)

    for name in SERVER_LOGGERS:
        server_logger = logging.getLogger(name)
        server_logger.handlers.clear()
        server_logger.propagate = True
