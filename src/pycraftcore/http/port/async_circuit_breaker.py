from typing import Protocol, ParamSpec

from pycraftcore.http.configuration.circuite_breaker_configuration import (
    CircuitBreakerSettings,
)

P = ParamSpec("P")


class AsyncCircuitBreaker(Protocol):
    def _can_attempt(self) -> bool: ...
    def _on_success(self) -> None: ...
    def _on_failure(self, exception: Exception) -> None: ...

    async def call(self, func, *args: P.args, **kwargs: P.kwargs): ...

    @property
    def settings(self) -> CircuitBreakerSettings: ...
