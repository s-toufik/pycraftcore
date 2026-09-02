from collections.abc import Awaitable
from typing import Any, Protocol, runtime_checkable

from pycraftcore.circuit_breaker.port.async_circuit_breaker import AsyncCircuitBreaker


@runtime_checkable
class AsyncResilientHttpClient(Protocol):
    def get(self, *args: Any, **kwargs: Any) -> Awaitable[Any]: ...
    def post(self, *args: Any, **kwargs: Any) -> Awaitable[Any]: ...

    @property
    def circuit_breaker(self) -> AsyncCircuitBreaker: ...