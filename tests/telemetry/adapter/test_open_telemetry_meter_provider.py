from unittest.mock import MagicMock, patch

from pycraftcore.telemetry.adapter.open_telemetry_meter_provider import (
    OpenTelemetryMeterProvider,
)


def test_provider_uses_console_exporter_when_no_otlp_endpoint():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.SdkMeterProvider"
        ) as mock_provider_cls,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.PeriodicExportingMetricReader"
        ) as mock_reader,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.ConsoleMetricExporter"
        ) as mock_console,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.OTLPMetricExporter"
        ) as mock_otlp,
    ):
        resource = MagicMock()

        OpenTelemetryMeterProvider(resource=resource)

        mock_console.assert_called_once()
        mock_otlp.assert_not_called()
        mock_reader.assert_called_once_with(mock_console.return_value)
        mock_provider_cls.assert_called_once_with(
            resource=resource, metric_readers=[mock_reader.return_value]
        )


def test_provider_uses_otlp_exporter_when_endpoint_given():
    with (
        patch("pycraftcore.telemetry.adapter.open_telemetry_meter_provider.SdkMeterProvider"),
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.PeriodicExportingMetricReader"
        ),
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.ConsoleMetricExporter"
        ) as mock_console,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.OTLPMetricExporter"
        ) as mock_otlp,
    ):
        OpenTelemetryMeterProvider(resource=MagicMock(), otlp_endpoint="http://collector:4317")

        mock_otlp.assert_called_once_with(endpoint="http://collector:4317", insecure=True)
        mock_console.assert_not_called()


def test_meter_delegates_to_provider():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.SdkMeterProvider"
        ) as mock_provider_cls,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.PeriodicExportingMetricReader"
        ),
        patch("pycraftcore.telemetry.adapter.open_telemetry_meter_provider.ConsoleMetricExporter"),
    ):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        provider = OpenTelemetryMeterProvider(resource=MagicMock())
        meter = provider.meter("svc")

        mock_provider.get_meter.assert_called_once_with("svc")
        assert meter is mock_provider.get_meter.return_value


def test_shutdown_delegates_to_provider():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.SdkMeterProvider"
        ) as mock_provider_cls,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_meter_provider.PeriodicExportingMetricReader"
        ),
        patch("pycraftcore.telemetry.adapter.open_telemetry_meter_provider.ConsoleMetricExporter"),
    ):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        provider = OpenTelemetryMeterProvider(resource=MagicMock())
        provider.shutdown()

        mock_provider.shutdown.assert_called_once()
