from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import Meter
from opentelemetry.sdk.metrics import MeterProvider as SdkMeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    MetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource


class OpenTelemetryMeterProvider:
    def __init__(self, resource: Resource, otlp_endpoint: str = "") -> None:
        reader = PeriodicExportingMetricReader(self._exporter(otlp_endpoint))
        self._provider = SdkMeterProvider(resource=resource, metric_readers=[reader])

    @staticmethod
    def _exporter(otlp_endpoint: str) -> MetricExporter:
        if not otlp_endpoint:
            return ConsoleMetricExporter()
        return OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)

    def meter(self, service_name: str) -> Meter:
        return self._provider.get_meter(service_name)

    def shutdown(self) -> None:
        self._provider.shutdown()
