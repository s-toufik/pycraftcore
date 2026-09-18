from typing import Protocol, runtime_checkable

from opentelemetry.trace import Tracer


@runtime_checkable
class TelemetryTraceProvider(Protocol):
    def tracer(self, service_name: str) -> Tracer: ...
    def shutdown(self) -> None: ...
