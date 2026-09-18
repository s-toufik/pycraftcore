from typing import Protocol, runtime_checkable

from opentelemetry.metrics import Meter


@runtime_checkable
class TelemetryMeterProvider(Protocol):
    def meter(self, service_name: str) -> Meter: ...
    def shutdown(self) -> None: ...
