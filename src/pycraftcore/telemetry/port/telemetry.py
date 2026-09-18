import logging
from typing import Protocol, runtime_checkable

from opentelemetry.metrics import Meter

from pycraftcore.telemetry.port.tracer import TelemetryTracer

__all__ = ["TelemetryProvider", "TelemetryTracer"]


@runtime_checkable
class TelemetryProvider(Protocol):
    def tracer(self, service_name: str) -> TelemetryTracer: ...
    def log_handler(self) -> logging.Handler: ...
    def meter(self, service_name: str) -> Meter: ...
    def shutdown(self) -> None: ...
