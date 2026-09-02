from typing import Self

import aiohttp
from httpx import AsyncBaseTransport

from pycraftcore.circuit_breaker.adapter.aiobreaker_circuit_breaker_policy import (
    AioBreakerCircuitBreakerPolicy,
)
from pycraftcore.circuit_breaker.port.async_circuit_breaker import AsyncCircuitBreaker
from pycraftcore.http.adapter.aiohttp_client import AioHttpClientFactory
from pycraftcore.http.adapter.httpx_client import HttpxClientFactory
from pycraftcore.http.port.async_http_client import AsyncHttpFactory
from pycraftcore.logger.port.logger import Logger
from pycraftcore.resilient_http.adapter.resilient_client import ResilientClient
from pycraftcore.resilient_http.configuration.resilient_http_configuration import (
    ResilientHttpSettings,
)
from pycraftcore.retry.adapter.tenacity_retry_policy import TenacityRetryPolicy
from pycraftcore.retry.port.retry import Retry
from pycraftcore.telemetry.port.telemetry import TelemetryTracer


class ResilientHttpClientFactory:

    def __init__(
        self,
        http_factory: AsyncHttpFactory,
        settings: ResilientHttpSettings | None = None,
        trace_manager: TelemetryTracer | None = None,
        logger: Logger | None = None,
    ) -> None:
        self._settings: ResilientHttpSettings = settings or ResilientHttpSettings()
        self._http_factory: AsyncHttpFactory = http_factory
        self._trace_manager: TelemetryTracer | None = trace_manager
        self._logger: Logger | None = logger

        self._circuit_breaker: AsyncCircuitBreaker = AioBreakerCircuitBreakerPolicy(
            self._settings.circuit_breaker, logger
        )
        self._retry: Retry = TenacityRetryPolicy(self._settings.retry, logger)

    @classmethod
    def with_httpx(
        cls,
        settings: ResilientHttpSettings | None = None,
        trace_manager: TelemetryTracer | None = None,
        logger: Logger | None = None,
        http_transport: AsyncBaseTransport | None = None,
    ) -> Self:
        resilient_settings = settings or ResilientHttpSettings()

        return cls(
            http_factory=HttpxClientFactory(
                http_client_settings=resilient_settings.http,
                logger=logger,
                http_transport=http_transport,
            ),
            settings=resilient_settings,
            trace_manager=trace_manager,
            logger=logger,
        )

    @classmethod
    def with_aiohttp(
        cls,
        settings: ResilientHttpSettings | None = None,
        trace_manager: TelemetryTracer | None = None,
        logger: Logger | None = None,
        connector: aiohttp.BaseConnector | None = None,
    ) -> Self:
        resilient_settings = settings or ResilientHttpSettings()

        return cls(
            http_factory=AioHttpClientFactory(
                http_client_settings=resilient_settings.http, connector=connector
            ),
            settings=resilient_settings,
            trace_manager=trace_manager,
            logger=logger,
        )

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def start(self) -> None:
        await self._http_factory.start()

    async def close(self) -> None:
        await self._http_factory.close()

    @property
    def settings(self) -> ResilientHttpSettings:
        return self._settings

    @property
    def circuit_breaker(self) -> AsyncCircuitBreaker:
        return self._circuit_breaker

    def create_client(self) -> ResilientClient:
        return ResilientClient(
            base_client=self._http_factory.create_client(),
            circuit_breaker=self._circuit_breaker,
            retry_policy=self._retry,
            trace_manager=self._trace_manager,
        )