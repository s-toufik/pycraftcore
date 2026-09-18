import logging
from typing import Protocol, runtime_checkable


@runtime_checkable
class TelemetryLoggerProvider(Protocol):
    def handler(self) -> logging.Handler: ...
    def shutdown(self) -> None: ...
