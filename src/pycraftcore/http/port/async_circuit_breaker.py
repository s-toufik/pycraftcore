from collections.abc import Awaitable, Callable
from typing import ParamSpec, Protocol, TypeVar, runtime_checkable

from pycraftcore.http.configuration.circuite_breaker_configuration import (
    CircuitBreakerSettings,
)

P = ParamSpec("P")
R = TypeVar("R")


@runtime_checkable
class AsyncCircuitBreaker(Protocol):
    def _can_attempt(self) -> bool: ...
    def _on_success(self) -> None: ...
    def _on_failure(self, exception: Exception) -> None: ...

    async def call(
        self,
        func: Callable[P, Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R: ...

    @property
    def settings(self) -> CircuitBreakerSettings: ...
