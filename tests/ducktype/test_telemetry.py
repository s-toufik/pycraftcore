from unittest.mock import MagicMock

from pycraftcore.telemetry.adapter.open_telemetry import (
    OpenTelemetryProvider,
    OpenTelemetryTracer,
)
from pycraftcore.telemetry.port.telemetry import TelemetryProvider, TelemetryTracer


def test_open_telemetry_tracer_satisfies_telemetry_tracer():
    tracer: TelemetryTracer = OpenTelemetryTracer(MagicMock(), "test-trace")

    assert isinstance(tracer, TelemetryTracer)


def test_open_telemetry_provider_satisfies_telemetry_provider():
    provider: TelemetryProvider = OpenTelemetryProvider(service_name="test-service")

    try:
        assert isinstance(provider, TelemetryProvider)
    finally:
        provider.shutdown()
