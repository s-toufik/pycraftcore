from typing import Self

import httpx
import pytest

from pycraftcore.circuit_breaker.adapter.aiobreaker_circuit_breaker_policy import (
    AioBreakerCircuitBreakerPolicy,
)
from pycraftcore.circuit_breaker.enum.circuit_breaker_status import CircuitState
from pycraftcore.circuit_breaker.exception.circuit_breaker_open_exception import (
    CircuitBreakerOpenException,
)
from pycraftcore.http.adapter.aiohttp_client import AioHttpClientFactory
from pycraftcore.http.adapter.httpx_client import HttpxClientFactory
from pycraftcore.http.configuration import ClientSettings, HttpClientSettings
from pycraftcore.resilient_http.adapter.resilient_client import ResilientClient
from pycraftcore.resilient_http.adapter.resilient_http_client_factory import (
    ResilientHttpClientFactory,
)
from pycraftcore.resilient_http.configuration.resilient_http_configuration import (
    ResilientHttpSettings,
)
from pycraftcore.retry.adapter.tenacity_retry_policy import TenacityRetryPolicy


@pytest.mark.asyncio
async def test_with_httpx_uses_an_httpx_backed_http_factory():
    async with ResilientHttpClientFactory.with_httpx() as factory:
        assert isinstance(factory._http_factory, HttpxClientFactory)
        client = factory.create_client()
        assert isinstance(client, ResilientClient)


@pytest.mark.asyncio
async def test_with_aiohttp_uses_an_aiohttp_backed_http_factory():
    async with ResilientHttpClientFactory.with_aiohttp() as factory:
        assert isinstance(factory._http_factory, AioHttpClientFactory)
        client = factory.create_client()
        assert isinstance(client, ResilientClient)


@pytest.mark.asyncio
async def test_defaults_settings_when_none_provided():
    async with ResilientHttpClientFactory.with_httpx() as factory:
        assert isinstance(factory.settings, ResilientHttpSettings)


@pytest.mark.asyncio
async def test_circuit_breaker_is_shared_across_clients_created_from_the_same_factory():
    async with ResilientHttpClientFactory.with_httpx() as factory:
        first = factory.create_client()
        second = factory.create_client()

        assert first.circuit_breaker is second.circuit_breaker
        assert first.circuit_breaker is factory.circuit_breaker


@pytest.mark.asyncio
async def test_circuit_breaker_state_is_shared_across_clients():
    # A failure recorded through one client's breaker call must be visible to
    # every other client created from the same factory -- they protect the
    # same downstream, so they must share breaker state.
    calls = {"n": 0}

    async def handler(request):
        calls["n"] += 1
        return httpx.Response(500, json={"err": "boom"})

    settings = ResilientHttpSettings(
        http=HttpClientSettings(client_params=ClientSettings(base_url="https://api.test.com"))
    )
    settings.circuit_breaker.failure_threshold = 1
    settings.retry.retry_count = 0
    settings.retry.retry_delay = 0.001
    settings.retry.max_retry_delay = 0.002

    async with ResilientHttpClientFactory.with_httpx(
        settings=settings, http_transport=httpx.MockTransport(handler)
    ) as factory:
        first = factory.create_client()
        second = factory.create_client()

        with pytest.raises(httpx.HTTPStatusError):
            await first.get("/health")

        assert second.circuit_breaker.state == CircuitState.OPEN
        with pytest.raises(CircuitBreakerOpenException):
            await second.get("/health")


@pytest.mark.asyncio
async def test_start_and_close_delegate_to_the_underlying_http_factory():
    factory = ResilientHttpClientFactory.with_httpx()

    await factory.start()
    assert factory._http_factory._client_instance.is_closed is False

    await factory.close()
    assert "_client_instance" not in factory._http_factory.__dict__


@pytest.mark.asyncio
async def test_context_manager_starts_and_closes():
    async with ResilientHttpClientFactory.with_httpx() as factory:
        client = factory.create_client()
        result_client_type = type(client)

    assert result_client_type is ResilientClient
    assert "_client_instance" not in factory._http_factory.__dict__


def test_init_builds_retry_and_circuit_breaker_from_settings():
    settings = ResilientHttpSettings()
    factory = ResilientHttpClientFactory(
        http_factory=HttpxClientFactory(http_client_settings=settings.http),
        settings=settings,
    )

    assert isinstance(factory._retry, TenacityRetryPolicy)
    assert factory._retry.settings is settings.retry
    assert isinstance(factory._circuit_breaker, AioBreakerCircuitBreakerPolicy)
    assert factory._circuit_breaker.settings is settings.circuit_breaker


@pytest.mark.asyncio
async def test_factory_satisfies_async_http_factory_lifecycle_protocol():
    factory = ResilientHttpClientFactory.with_httpx()

    result: Self = await factory.__aenter__()
    assert result is factory

    await factory.__aexit__(None, None, None)
