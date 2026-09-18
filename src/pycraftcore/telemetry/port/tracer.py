from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, Protocol, TypeVar, runtime_checkable

P = ParamSpec("P")
R = TypeVar("R")


@runtime_checkable
class TelemetryTracer(Protocol):
    def trace(
        self, span_name: str, static_attributes: dict[str, Any]
    ) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]: ...
