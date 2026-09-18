from unittest.mock import MagicMock, patch

from pycraftcore.http.context.request_context import request_id_context
from pycraftcore.telemetry.adapter.open_telemetry_provider import (
    OpenTelemetryTraceProvider,
    RequestIdSpanProcessor,
)


def test_provider_uses_console_exporter_when_no_otlp_endpoint():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.SdkTracerProvider"
        ) as mock_provider_cls,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.BatchSpanProcessor"
        ) as mock_bsp,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.ConsoleSpanExporter"
        ) as mock_console,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.OTLPSpanExporter"
        ) as mock_otlp,
        patch("pycraftcore.telemetry.adapter.open_telemetry_provider.trace.set_tracer_provider"),
    ):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        OpenTelemetryTraceProvider(resource=MagicMock())

        mock_console.assert_called_once()
        mock_otlp.assert_not_called()
        mock_provider.add_span_processor.assert_called_with(mock_bsp.return_value)
        assert mock_provider.add_span_processor.call_count == 2
        first_processor = mock_provider.add_span_processor.call_args_list[0].args[0]
        assert isinstance(first_processor, RequestIdSpanProcessor)


def test_provider_uses_otlp_exporter_when_endpoint_given():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.SdkTracerProvider"
        ) as mock_provider_cls,
        patch("pycraftcore.telemetry.adapter.open_telemetry_provider.BatchSpanProcessor"),
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.ConsoleSpanExporter"
        ) as mock_console,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.OTLPSpanExporter"
        ) as mock_otlp,
        patch("pycraftcore.telemetry.adapter.open_telemetry_provider.trace.set_tracer_provider"),
    ):
        mock_provider_cls.return_value = MagicMock()

        OpenTelemetryTraceProvider(
            resource=MagicMock(),
            otlp_endpoint="http://collector:4317",
        )

        mock_otlp.assert_called_once_with(endpoint="http://collector:4317", insecure=True)
        mock_console.assert_not_called()


def test_provider_sets_the_global_tracer_provider():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.SdkTracerProvider"
        ) as mock_provider_cls,
        patch("pycraftcore.telemetry.adapter.open_telemetry_provider.BatchSpanProcessor"),
        patch("pycraftcore.telemetry.adapter.open_telemetry_provider.ConsoleSpanExporter"),
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.trace.set_tracer_provider"
        ) as mock_set,
    ):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        OpenTelemetryTraceProvider(resource=MagicMock())

        mock_set.assert_called_once_with(mock_provider)


def test_tracer_delegates_to_the_global_otel_api():
    with patch(
        "pycraftcore.telemetry.adapter.open_telemetry_provider.trace.get_tracer"
    ) as mock_get_tracer:
        fake_tracer = MagicMock()
        mock_get_tracer.return_value = fake_tracer

        tracer = OpenTelemetryTraceProvider.tracer("svc")

        mock_get_tracer.assert_called_once_with("svc")
        assert tracer is fake_tracer


def test_shutdown_delegates_to_provider():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_provider.SdkTracerProvider"
        ) as mock_provider_cls,
        patch("pycraftcore.telemetry.adapter.open_telemetry_provider.BatchSpanProcessor"),
        patch("pycraftcore.telemetry.adapter.open_telemetry_provider.ConsoleSpanExporter"),
        patch("pycraftcore.telemetry.adapter.open_telemetry_provider.trace.set_tracer_provider"),
    ):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        provider = OpenTelemetryTraceProvider(resource=MagicMock())
        provider.shutdown()

        mock_provider.shutdown.assert_called_once()


def test_request_id_span_processor_sets_attribute_when_request_id_is_set():
    span = MagicMock()
    token = request_id_context.set("req-456")
    try:
        RequestIdSpanProcessor().on_start(span)
    finally:
        request_id_context.reset(token)

    span.set_attribute.assert_called_once_with("request_id", "req-456")


def test_request_id_span_processor_does_nothing_when_request_id_is_unset():
    span = MagicMock()

    assert request_id_context.get() is None
    RequestIdSpanProcessor().on_start(span)

    span.set_attribute.assert_not_called()
