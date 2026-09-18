import logging
from typing import cast

from opentelemetry.attributes import BoundedAttributes
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.sdk._logs import LoggerProvider as SdkLoggerProvider
from opentelemetry.sdk._logs import LogRecordProcessor, ReadWriteLogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogRecordExporter
from opentelemetry.sdk.resources import Resource

from pycraftcore.http.context.request_context import request_id_context


class RequestIdLogRecordProcessor(LogRecordProcessor):
    def on_emit(self, log_record: ReadWriteLogRecord) -> None:
        request_id = request_id_context.get()
        if request_id:
            # ReadWriteLogRecord.__post_init__ always replaces attributes with a
            # mutable BoundedAttributes; the SDK's own type just declares the
            # read-only Mapping shape callers are expected to see.
            attributes = cast(BoundedAttributes, log_record.log_record.attributes)
            attributes["request_id"] = request_id

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


class OpenTelemetryLoggerProvider:
    def __init__(self, resource: Resource, otlp_endpoint: str = "") -> None:
        provider = SdkLoggerProvider(resource=resource)
        provider.add_log_record_processor(RequestIdLogRecordProcessor())
        self._configure_exporter(otlp_endpoint, provider)
        self._provider = provider

    @staticmethod
    def _configure_exporter(otlp_endpoint: str, provider: SdkLoggerProvider) -> None:
        if not otlp_endpoint:
            provider.add_log_record_processor(BatchLogRecordProcessor(ConsoleLogRecordExporter()))
        else:
            provider.add_log_record_processor(
                BatchLogRecordProcessor(
                    OTLPLogExporter(
                        endpoint=otlp_endpoint,
                        insecure=True,
                    )
                )
            )

    def handler(self) -> logging.Handler:
        return LoggingHandler(level=logging.NOTSET, logger_provider=self._provider)

    def shutdown(self) -> None:
        self._provider.shutdown()
