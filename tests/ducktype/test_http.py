from unittest.mock import MagicMock

from httpx import AsyncClient

from pycraftcore.http.adapter.aiohttp_client import AioHttpClient, AioHttpClientFactory
from pycraftcore.http.adapter.circuit_breaker_policy import CircuitBreakerPolicy
from pycraftcore.http.adapter.httpx_client import HttpxClient, HttpxClientFactory
from pycraftcore.http.adapter.resilient_client import ResilientClient
from pycraftcore.http.adapter.retry_policy import RetryPolicy
from pycraftcore.http.port.async_circuit_breaker import AsyncCircuitBreaker
from pycraftcore.http.port.async_http_client import AsyncHttpClient, AsyncHttpFactory
from pycraftcore.http.port.async_resilient_http_client import AsyncResilientHttpClient
from pycraftcore.http.port.retry import Retry


def test_circuit_breaker_policy_satisfies_async_circuit_breaker():
    breaker: AsyncCircuitBreaker = CircuitBreakerPolicy()

    assert isinstance(breaker, AsyncCircuitBreaker)


def test_retry_policy_satisfies_retry():
    retry: Retry = RetryPolicy()

    assert isinstance(retry, Retry)


def test_aiohttp_client_factory_satisfies_async_http_factory():
    factory: AsyncHttpFactory[AsyncClient] = AioHttpClientFactory()

    assert isinstance(factory, AsyncHttpFactory)


def test_httpx_client_factory_satisfies_async_http_factory():
    factory: AsyncHttpFactory[AsyncClient] = HttpxClientFactory()

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
        circuit_breaker=CircuitBreakerPolicy(),
        retry_policy=RetryPolicy(),
        trace_manager=MagicMock(),
    )

    assert isinstance(client, AsyncResilientHttpClient)
