from unittest.mock import MagicMock

import httpx

from pycraftcore.circuit_breaker.adapter.aiobreaker_circuit_breaker_policy import (
    AioBreakerCircuitBreakerPolicy,
)
from pycraftcore.circuit_breaker.port.async_circuit_breaker import AsyncCircuitBreaker
from pycraftcore.http.adapter.aiohttp_client import AioHttpClient, AioHttpClientFactory
from pycraftcore.http.adapter.httpx_client import HttpxClient, HttpxClientFactory
from pycraftcore.http.port.async_http_client import AsyncHttpClient, AsyncHttpFactory
from pycraftcore.resilient_http.adapter.resilient_client import ResilientClient
from pycraftcore.resilient_http.adapter.resilient_transport import ResilientTransport
from pycraftcore.resilient_http.port.async_resilient_http_client import AsyncResilientHttpClient
from pycraftcore.retry.adapter.tenacity_retry_policy import TenacityRetryPolicy
from pycraftcore.retry.port.retry import Retry


def test_aiobreaker_circuit_breaker_policy_satisfies_async_circuit_breaker():
    breaker: AsyncCircuitBreaker = AioBreakerCircuitBreakerPolicy()

    assert isinstance(breaker, AsyncCircuitBreaker)


def test_tenacity_retry_policy_satisfies_retry():
    retry: Retry = TenacityRetryPolicy()

    assert isinstance(retry, Retry)


def test_aiohttp_client_factory_satisfies_async_http_factory():
    factory: AsyncHttpFactory = AioHttpClientFactory()

    assert isinstance(factory, AsyncHttpFactory)


def test_httpx_client_factory_satisfies_async_http_factory():
    factory: AsyncHttpFactory = HttpxClientFactory()

    assert isinstance(factory, AsyncHttpFactory)


def test_aiohttp_client_satisfies_async_http_client():
    client: AsyncHttpClient = AioHttpClient(base_url="https://api.test.com", session=MagicMock())

    assert isinstance(client, AsyncHttpClient)


def test_httpx_client_satisfies_async_http_client():
    client: AsyncHttpClient = HttpxClient(MagicMock())

    assert isinstance(client, AsyncHttpClient)


def test_resilient_client_satisfies_async_resilient_http_client():
    client: AsyncResilientHttpClient = ResilientClient(
        base_client=MagicMock(),
        circuit_breaker=AioBreakerCircuitBreakerPolicy(),
        retry_policy=TenacityRetryPolicy(),
        trace_manager=MagicMock(),
    )

    assert isinstance(client, AsyncResilientHttpClient)


def test_resilient_transport_satisfies_httpx_async_base_transport():
    transport = ResilientTransport(
        transport=MagicMock(spec=httpx.AsyncBaseTransport),
        circuit_breaker=AioBreakerCircuitBreakerPolicy(),
        retry_policy=TenacityRetryPolicy(),
    )

    assert isinstance(transport, httpx.AsyncBaseTransport)
