from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode, Tracer

from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.http.context.request_context import request_id_context

P = ParamSpec("P")
R = TypeVar("R")
TraceType = Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]


class OpenTelemetryProvider:
    def __init__(
        self,
        service_name: str,
        environment: RunTypeEnvironment = RunTypeEnvironment.debug,
        otlp_endpoint: str | None = None,
    ) -> None:

        self._service_name = service_name
        self._environment = environment
        self._otlp_endpoint = otlp_endpoint or ""

        resource = Resource.create(
            {
                SERVICE_NAME: service_name,
                "deployment.environment": environment.value,
            }
        )

        provider = TracerProvider(resource=resource)
        self._configure_exporter(self._otlp_endpoint, provider)
        trace.set_tracer_provider(provider)
        self._provider = provider

    @staticmethod
    def _configure_exporter(otlp_endpoint: str, provider: TracerProvider) -> None:
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
    def tracer(service_name: str) -> OpenTelemetryTracer:
        return OpenTelemetryTracer(trace.get_tracer(service_name), service_name)

    def shutdown(self) -> None:
        self._provider.shutdown()


class OpenTelemetryTracer:
    def __init__(self, tracer: Tracer, trace_name: str) -> None:
        self._tracer = tracer
        self._trace_name = trace_name

    @property
    def tracer(self) -> Tracer:
        return self._tracer

    def trace(self, span_name: str, static_attributes: dict[str, Any]) -> TraceType:
        def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                with self._tracer.start_as_current_span(span_name) as span:
                    self._enrich_span(span, static_attributes)
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result

                    except Exception:
                        span.set_status(Status(StatusCode.ERROR))
                        raise

            return wrapper

        return decorator

    def _enrich_span(self, span, static_attributes: dict[str, Any]) -> None:

        request_id = request_id_context.get()

        if request_id:
            span.set_attribute("request_id", request_id)
            span.set_attribute("tracer_name", self._trace_name)

        for k, v in static_attributes.items():
            span.set_attribute(k, v.__str__())
