from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from opentelemetry.trace import Span, Status, StatusCode, Tracer

from pycraftcore.http.context.request_context import request_id_context

P = ParamSpec("P")
R = TypeVar("R")
TraceType = Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]


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

    def _enrich_span(self, span: Span, static_attributes: dict[str, Any]) -> None:

        request_id = request_id_context.get()

        if request_id:
            span.set_attribute("request_id", request_id)
            span.set_attribute("tracer_name", self._trace_name)

        for k, v in static_attributes.items():
            span.set_attribute(k, v.__str__())
