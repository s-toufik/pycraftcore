from typing import Any, Final

from httpx import AsyncBaseTransport, HTTPStatusError, Request, Response

from pycraftcore.circuit_breaker.port.async_circuit_breaker import AsyncCircuitBreaker
from pycraftcore.retry.port.retry import Retry
from pycraftcore.telemetry.adapter.null_telemetry import NullTelemetryTracer
from pycraftcore.telemetry.port.telemetry import TelemetryTracer


class TransportStatusError(HTTPStatusError):

    def __init__(self, request: Request, response: Response) -> None:
        super().__init__(
            f"HTTP {response.status_code} for {request.url}",
            request=request,
            response=response,
        )


class ResilientTransport(AsyncBaseTransport):
   
    def __init__(
        self,
        transport: AsyncBaseTransport,
        circuit_breaker: AsyncCircuitBreaker,
        retry_policy: Retry,
        trace_manager: TelemetryTracer | None = None,
    ) -> None:
        self._transport: Final = transport
        self._circuit_breaker: Final = circuit_breaker
        self._retry: Final = retry_policy
        self._trace: Final = trace_manager or NullTelemetryTracer()

        retryable = self._retry.decorator(self._send)

        @self._trace.trace(span_name="http.request", static_attributes=self._span_attributes())
        async def pipeline(request: Request) -> Response:
            return await self._circuit_breaker.call(retryable, request)

        self._pipeline = pipeline

    async def handle_async_request(self, request: Request) -> Response:
        # Buffers the body so a retried attempt can replay it.
        await request.aread()

        try:
            return await self._pipeline(request)

        except TransportStatusError as error:
            return error.response

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def _send(self, request: Request) -> Response:
        response: Response = await self._transport.handle_async_request(request)

        if response.status_code >= 400:
            # The body must be drained before another attempt reuses the
            # connection, and it is what the caller will read afterwards.
            await response.aread()
            raise TransportStatusError(request, response)

        return response

    def _span_attributes(self) -> dict[str, Any]:
        retry = self._retry.settings
        breaker = self._circuit_breaker.settings

        return {
            "retry.attempts": retry.attempts,
            "retry.delay": retry.retry_delay,
            "retry.max_delay": retry.max_retry_delay,
            "circuit_breaker.name": breaker.name,
            "circuit_breaker.failure_threshold": breaker.failure_threshold,
            "circuit_breaker.recovery_timeout": breaker.recovery_timeout,
        }