import logging
from collections.abc import Iterator

import pytest

from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.logger.configuration import (
    NO_REQUEST_ID,
    RequestIdFilter,
    _ConsoleHandler,
    configure_logging,
)


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    uvicorn = logging.getLogger("uvicorn.access")
    uvicorn_handlers, uvicorn_propagate = uvicorn.handlers[:], uvicorn.propagate
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    uvicorn.handlers[:] = uvicorn_handlers
    uvicorn.propagate = uvicorn_propagate


def _console_handlers() -> list[logging.Handler]:
    return [h for h in logging.getLogger().handlers if isinstance(h, _ConsoleHandler)]


def _format(message: str) -> str:
    handler = _console_handlers()[0]
    record = logging.LogRecord(
        "app", logging.INFO, "/src/app/controller.py", 12, message, None, None, "run"
    )
    handler.filter(record)
    return handler.format(record)


def test_a_line_carries_the_request_id_of_the_current_context() -> None:
    configure_logging()
    token = request_id_context.set("req-42")
    try:
        line = _format("stream accepted")
    finally:
        request_id_context.reset(token)

    assert "| INFO     | req-42 | controller:run:12 - stream accepted" in line


def test_a_line_outside_a_request_shows_a_placeholder() -> None:
    configure_logging()

    assert f"| {NO_REQUEST_ID} |" in _format("booted")


def test_the_placeholder_is_not_written_on_the_record() -> None:
    # The OTLP handler exports extra record fields: it must not receive a fake request id.
    record = logging.LogRecord("app", logging.INFO, "/src/app.py", 1, "booted", None, None)

    RequestIdFilter().filter(record)

    assert not hasattr(record, "request_id")


def test_calling_it_twice_keeps_a_single_console_handler() -> None:
    configure_logging("INFO")
    configure_logging("DEBUG")

    assert len(_console_handlers()) == 1
    assert logging.getLogger().level == logging.DEBUG


def test_noisy_libraries_stay_at_warning_even_in_debug() -> None:
    configure_logging("DEBUG")

    assert logging.getLogger("httpx").level == logging.WARNING


def test_uvicorn_lines_go_through_the_shared_format() -> None:
    logging.getLogger("uvicorn.access").addHandler(logging.StreamHandler())
    logging.getLogger("uvicorn.access").propagate = False

    configure_logging()

    assert logging.getLogger("uvicorn.access").handlers == []
    assert logging.getLogger("uvicorn.access").propagate is True
