import logging
from unittest.mock import MagicMock, patch

from pycraftcore.http.context.request_context import request_id_context
from pycraftcore.telemetry.adapter.open_telemetry_logger_provider import (
    OpenTelemetryLoggerProvider,
    RequestIdLogRecordProcessor,
)


def test_provider_uses_console_exporter_when_no_otlp_endpoint():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.SdkLoggerProvider"
        ) as mock_provider_cls,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.BatchLogRecordProcessor"
        ) as mock_blrp,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.ConsoleLogRecordExporter"
        ) as mock_console,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.OTLPLogExporter"
        ) as mock_otlp,
    ):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        OpenTelemetryLoggerProvider(resource=MagicMock())

        mock_console.assert_called_once()
        mock_otlp.assert_not_called()
        mock_provider.add_log_record_processor.assert_called_with(mock_blrp.return_value)
        assert mock_provider.add_log_record_processor.call_count == 2
        first_processor = mock_provider.add_log_record_processor.call_args_list[0].args[0]
        assert isinstance(first_processor, RequestIdLogRecordProcessor)


def test_provider_uses_otlp_exporter_when_endpoint_given():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.SdkLoggerProvider"
        ) as mock_provider_cls,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.BatchLogRecordProcessor"
        ),
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.ConsoleLogRecordExporter"
        ) as mock_console,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.OTLPLogExporter"
        ) as mock_otlp,
    ):
        mock_provider_cls.return_value = MagicMock()

        OpenTelemetryLoggerProvider(
            resource=MagicMock(),
            otlp_endpoint="http://collector:4317",
        )

        mock_otlp.assert_called_once_with(endpoint="http://collector:4317", insecure=True)
        mock_console.assert_not_called()


def test_handler_returns_a_logging_handler_bound_to_the_provider():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.SdkLoggerProvider"
        ) as mock_provider_cls,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.BatchLogRecordProcessor"
        ),
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.ConsoleLogRecordExporter"
        ),
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.LoggingHandler"
        ) as mock_handler_cls,
    ):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider
        mock_handler_cls.return_value = MagicMock(spec=logging.Handler)

        provider = OpenTelemetryLoggerProvider(resource=MagicMock())
        handler = provider.handler()

        mock_handler_cls.assert_called_once_with(
            level=logging.NOTSET, logger_provider=mock_provider
        )
        assert handler is mock_handler_cls.return_value


def test_shutdown_delegates_to_provider():
    with (
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.SdkLoggerProvider"
        ) as mock_provider_cls,
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.BatchLogRecordProcessor"
        ),
        patch(
            "pycraftcore.telemetry.adapter.open_telemetry_logger_provider.ConsoleLogRecordExporter"
        ),
    ):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        provider = OpenTelemetryLoggerProvider(resource=MagicMock())
        provider.shutdown()

        mock_provider.shutdown.assert_called_once()


def make_fake_log_record():
    log_record = MagicMock()
    log_record.attributes = {}
    wrapper = MagicMock()
    wrapper.log_record = log_record
    return wrapper


def test_request_id_processor_sets_attribute_when_request_id_is_set():
    record = make_fake_log_record()
    token = request_id_context.set("req-456")
    try:
        RequestIdLogRecordProcessor().on_emit(record)
    finally:
        request_id_context.reset(token)

    assert record.log_record.attributes["request_id"] == "req-456"


def test_request_id_processor_does_nothing_when_request_id_is_unset():
    record = make_fake_log_record()

    assert request_id_context.get() is None
    RequestIdLogRecordProcessor().on_emit(record)

    assert "request_id" not in record.log_record.attributes
