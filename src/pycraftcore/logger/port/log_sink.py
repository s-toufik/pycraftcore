import logging
from typing import Protocol, runtime_checkable


@runtime_checkable
class LogSink(Protocol):
    def attach(self, handler: logging.Handler) -> None: ...
