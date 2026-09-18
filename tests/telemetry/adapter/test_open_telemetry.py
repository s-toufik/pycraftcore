from unittest.mock import MagicMock, patch

from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.telemetry.adapter.open_telemetry import OpenTelemetryProvider
from pycraftcore.telemetry.adapter.open_telemetry_tracer import OpenTelemetryTracer

MODULE = "pycraftcore.telemetry.adapter.open_telemetry"


def build_provider(**kwargs):
    with (
        patch(f"{MODULE}.OpenTelemetryTraceProvider") as mock_trace_provider_cls,
        patch(f"{MODULE}.OpenTelemetryLoggerProvider") as mock_logger_provider_cls,
        patch(f"{MODULE}.OpenTelemetryMeterProvider") as mock_meter_provider_cls,
        patch(f"{MODULE}.Resource") as mock_resource,
    ):
        provider = OpenTelemetryProvider(service_name="svc", **kwargs)
        return (
            provider,
            mock_trace_provider_cls,
            mock_logger_provider_cls,
            mock_meter_provider_cls,
            mock_resource,
        )


def test_init_builds_one_shared_resource_and_wires_all_three_sub_providers():
    provider, trace_cls, logger_cls, meter_cls, resource_cls = build_provider(
        environment=RunTypeEnvironment.deploy,
        otlp_endpoint="http://collector:4317",
    )

    resource = resource_cls.create.return_value
    trace_cls.assert_called_once_with(resource, "http://collector:4317")
    logger_cls.assert_called_once_with(resource, "http://collector:4317")
    meter_cls.assert_called_once_with(resource, "http://collector:4317")
    assert provider._trace_provider is trace_cls.return_value
    assert provider._logger_provider is logger_cls.return_value
    assert provider._meter_provider is meter_cls.return_value


def test_tracer_wraps_the_trace_provider_tracer_in_an_open_telemetry_tracer():
    provider, trace_cls, *_ = build_provider()
    fake_raw_tracer = MagicMock()
    trace_cls.return_value.tracer.return_value = fake_raw_tracer

    tracer = provider.tracer("svc")

    trace_cls.return_value.tracer.assert_called_once_with("svc")
    assert isinstance(tracer, OpenTelemetryTracer)
    assert tracer.tracer is fake_raw_tracer


def test_log_handler_delegates_to_the_logger_provider():
    provider, _, logger_cls, *_ = build_provider()

    handler = provider.log_handler()

    logger_cls.return_value.handler.assert_called_once_with()
    assert handler is logger_cls.return_value.handler.return_value


def test_meter_delegates_to_the_meter_provider():
    provider, _, _, meter_cls, _ = build_provider()

    meter = provider.meter("svc")

    meter_cls.return_value.meter.assert_called_once_with("svc")
    assert meter is meter_cls.return_value.meter.return_value


def test_shutdown_shuts_down_all_three_sub_providers():
    provider, trace_cls, logger_cls, meter_cls, _ = build_provider()

    provider.shutdown()

    trace_cls.return_value.shutdown.assert_called_once()
    logger_cls.return_value.shutdown.assert_called_once()
    meter_cls.return_value.shutdown.assert_called_once()
