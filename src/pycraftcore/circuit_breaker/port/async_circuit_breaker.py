from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, Protocol, TypeVar, runtime_checkable

from pycraftcore.circuit_breaker.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.circuit_breaker.enum.circuit_breaker_status import CircuitState

P = ParamSpec("P")
R = TypeVar("R")


@runtime_checkable
class AsyncCircuitBreaker(Protocol):
    async def call(
        self,
        func: Callable[P, Coroutine[Any, Any, R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R: ...

    @property
    def settings(self) -> CircuitBreakerSettings: ...

    @property
    def state(self) -> CircuitState: ...