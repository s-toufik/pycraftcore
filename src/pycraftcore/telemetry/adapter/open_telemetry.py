import logging

from opentelemetry.metrics import Meter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.telemetry.adapter.open_telemetry_logger_provider import (
    OpenTelemetryLoggerProvider,
)
from pycraftcore.telemetry.adapter.open_telemetry_meter_provider import (
    OpenTelemetryMeterProvider,
)
from pycraftcore.telemetry.adapter.open_telemetry_provider import OpenTelemetryTraceProvider
from pycraftcore.telemetry.adapter.open_telemetry_tracer import OpenTelemetryTracer
from pycraftcore.telemetry.port.tracer import TelemetryTracer


class OpenTelemetryProvider:
    def __init__(
        self,
        service_name: str,
        environment: RunTypeEnvironment = RunTypeEnvironment.debug,
        otlp_endpoint: str | None = None,
    ) -> None:

        self._otlp_endpoint = otlp_endpoint or ""

        resource = Resource.create(
            {
                SERVICE_NAME: service_name,
                "deployment.environment": environment.value,
            }
        )

        self._trace_provider = OpenTelemetryTraceProvider(resource, self._otlp_endpoint)
        self._logger_provider = OpenTelemetryLoggerProvider(resource, self._otlp_endpoint)
        self._meter_provider = OpenTelemetryMeterProvider(resource, self._otlp_endpoint)

    def tracer(self, service_name: str) -> TelemetryTracer:
        return OpenTelemetryTracer(self._trace_provider.tracer(service_name), service_name)

    def log_handler(self) -> logging.Handler:
        return self._logger_provider.handler()

    def meter(self, service_name: str) -> Meter:
        return self._meter_provider.meter(service_name)

    def shutdown(self) -> None:
        self._trace_provider.shutdown()
        self._logger_provider.shutdown()
        self._meter_provider.shutdown()
