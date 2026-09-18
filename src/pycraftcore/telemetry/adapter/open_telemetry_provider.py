from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Span, SpanProcessor
from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Tracer

from pycraftcore.http.context.request_context import request_id_context


class RequestIdSpanProcessor(SpanProcessor):
    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        request_id = request_id_context.get()
        if request_id:
            span.set_attribute("request_id", request_id)


class OpenTelemetryTraceProvider:
    def __init__(self, resource: Resource, otlp_endpoint: str = "") -> None:
        provider = SdkTracerProvider(resource=resource)
        provider.add_span_processor(RequestIdSpanProcessor())
        self._configure_exporter(otlp_endpoint, provider)
        trace.set_tracer_provider(provider)
        self._provider = provider

    @staticmethod
    def _configure_exporter(otlp_endpoint: str, provider: SdkTracerProvider) -> None:
        if not otlp_endpoint:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        else:
            provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(
                        endpoint=otlp_endpoint,
                        insecure=True,
                    )
                )
            )

    @staticmethod
    def tracer(service_name: str) -> Tracer:
        return trace.get_tracer(service_name)

    def shutdown(self) -> None:
        self._provider.shutdown()
