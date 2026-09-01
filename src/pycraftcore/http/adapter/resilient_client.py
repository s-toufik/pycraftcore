from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import Any, Final, ParamSpec, TypeVar

from pycraftcore.http.enum.http_method import HttpMethod
from pycraftcore.http.port.async_circuit_breaker import AsyncCircuitBreaker
from pycraftcore.http.port.async_http_client import AsyncHttpClient
from pycraftcore.http.port.retry import Retry
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
        trace_manager: TelemetryTracer,
    ) -> None:

        self._base_client: Final = base_client
        self._circuit_breaker: Final = circuit_breaker
        self._retry: Final = retry_policy
        self._trace: Final = trace_manager

        self.get = self._build_pipeline(
            method_name=HttpMethod.GET.value, method=self._base_client.get
        )
        self.post = self._build_pipeline(
            method_name=HttpMethod.POST.value, method=self._base_client.post
        )

    def _build_pipeline(
        self, method_name: str, method: Callable[P, Awaitable[R]]
    ) -> Callable[P, Awaitable[R]]:

        @self._trace.trace(
            span_name=method_name,
            static_attributes={
                "HttpMethod": method_name,
                **asdict(self._retry.settings),
                **asdict(self._circuit_breaker.settings),
            },
        )
        @self._retry.decorator
        async def wrapped(*args: P.args, **kwargs: P.kwargs):
            async def execute():
                return await method(*args, **kwargs)

            return await self._circuit_breaker.call(execute)

        return wrapped
