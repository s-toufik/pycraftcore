import ssl

from httpx import AsyncBaseTransport, AsyncClient, AsyncHTTPTransport, Limits, Timeout

from pycraftcore.circuit_breaker.adapter.aiobreaker_circuit_breaker_policy import (
    AioBreakerCircuitBreakerPolicy,
)
from pycraftcore.circuit_breaker.port.async_circuit_breaker import AsyncCircuitBreaker
from pycraftcore.logger.port.logger import Logger
from pycraftcore.resilient_http.adapter.resilient_transport import ResilientTransport
from pycraftcore.resilient_http.configuration.resilient_http_configuration import (
    ResilientHttpSettings,
)
from pycraftcore.retry.adapter.tenacity_retry_policy import TenacityRetryPolicy
from pycraftcore.retry.port.retry import Retry
from pycraftcore.telemetry.port.telemetry import TelemetryTracer


class ResilientTransportFactory:

    def __init__(
        self,
        settings: ResilientHttpSettings | None = None,
        trace_manager: TelemetryTracer | None = None,
        logger: Logger | None = None,
    ) -> None:
        self._settings: ResilientHttpSettings = settings or ResilientHttpSettings()
        self._trace_manager: TelemetryTracer | None = trace_manager

        self._circuit_breaker: AsyncCircuitBreaker = AioBreakerCircuitBreakerPolicy(
            self._settings.circuit_breaker, logger
        )
        self._retry: Retry = TenacityRetryPolicy(self._settings.retry, logger)

    @property
    def circuit_breaker(self) -> AsyncCircuitBreaker:
        return self._circuit_breaker

    def create_transport(self, transport: AsyncBaseTransport | None = None) -> ResilientTransport:
        return ResilientTransport(
            transport=transport or self._base_transport(),
            circuit_breaker=self._circuit_breaker,
            retry_policy=self._retry,
            trace_manager=self._trace_manager,
        )

    def create_async_client(self, transport: AsyncBaseTransport | None = None) -> AsyncClient:
        return AsyncClient(
            base_url=self._settings.http.client_params.base_url or "",
            timeout=Timeout(self._settings.http.limits.timeout),
            limits=self._limits(),
            transport=self.create_transport(transport),
        )

    def _base_transport(self) -> AsyncBaseTransport:
        return AsyncHTTPTransport(retries=0, verify=self._verify())

    def _limits(self) -> Limits:
        return Limits(
            max_connections=self._settings.http.limits.max_connections,
            max_keepalive_connections=self._settings.http.limits.max_keepalive_connections,
            keepalive_expiry=self._settings.http.limits.keep_alive_timeout,
        )

    def _verify(self) -> bool | ssl.SSLContext:
        if certificate_path := self._settings.http.security.certificate:
            context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            context.load_verify_locations(cafile=certificate_path)
            if tls_cipher_spec := self._settings.http.security.tls_cipher_spec:
                context.set_ciphers(tls_cipher_spec)
            return context

        return True