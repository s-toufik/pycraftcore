from typing import Protocol, Callable, Awaitable, ParamSpec, TypeVar, Any

P = ParamSpec("P")
R = TypeVar("R")


class TelemetryTracer(Protocol):
    def trace(
        self, span_name: str, static_attributes: dict[str, Any]
    ) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]: ...


class TelemetryProvider(Protocol):
    def tracer(self, service_name: str) -> TelemetryTracer: ...
    def shutdown(self) -> None: ...
