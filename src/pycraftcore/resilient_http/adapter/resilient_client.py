import functools
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Final, ParamSpec, TypeVar

from pycraftcore.circuit_breaker.port.async_circuit_breaker import AsyncCircuitBreaker
from pycraftcore.http.enum.http_method import HttpMethod
from pycraftcore.http.port.async_http_client import AsyncHttpClient
from pycraftcore.retry.port.retry import Retry
from pycraftcore.telemetry.adapter.null_telemetry import NullTelemetryTracer
from pycraftcore.telemetry.port.telemetry import TelemetryTracer

P = ParamSpec("P")
R = TypeVar("R")


class ResilientClient:
    get: Callable[..., Awaitable[Any]]
    post: Callable[..., Awaitable[Any]]

    def __init__(
        self,
        base_client: AsyncHttpClient,
        circuit_breaker: AsyncCircuitBreaker,
        retry_policy: Retry,
        trace_manager: TelemetryTracer | None = None,
    ) -> None:

        self._base_client: Final = base_client
        self._circuit_breaker: Final = circuit_breaker
        self._retry: Final = retry_policy
        self._trace: Final = trace_manager or NullTelemetryTracer()

        self.get = self._build_pipeline(
            method_name=HttpMethod.GET.value, method=self._base_client.get
        )
        self.post = self._build_pipeline(
            method_name=HttpMethod.POST.value, method=self._base_client.post
        )

    @property
    def circuit_breaker(self) -> AsyncCircuitBreaker:
        return self._circuit_breaker

    def _build_pipeline(
        self, method_name: str, method: Callable[P, Coroutine[Any, Any, R]]
    ) -> Callable[P, Awaitable[R]]:

        retryable: Callable[P, Coroutine[Any, Any, R]] = self._retry.decorator(method)

        @self._trace.trace(
            span_name=method_name, static_attributes=self._span_attributes(method_name)
        )
        @functools.wraps(method)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            return await self._circuit_breaker.call(retryable, *args, **kwargs)

        return wrapped

    def _span_attributes(self, method_name: str) -> dict[str, Any]:
        retry = self._retry.settings
        breaker = self._circuit_breaker.settings

        return {
            "HttpMethod": method_name,
            "retry.attempts": retry.attempts,
            "retry.delay": retry.retry_delay,
            "retry.max_delay": retry.max_retry_delay,
            "circuit_breaker.name": breaker.name,
            "circuit_breaker.failure_threshold": breaker.failure_threshold,
            "circuit_breaker.recovery_timeout": breaker.recovery_timeout,
        }
