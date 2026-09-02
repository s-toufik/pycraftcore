from typing import Any

import pytest

from pycraftcore.circuit_breaker.adapter.aiobreaker_circuit_breaker_policy import (
    AioBreakerCircuitBreakerPolicy,
)
from pycraftcore.circuit_breaker.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.circuit_breaker.enum.circuit_breaker_status import CircuitState
from pycraftcore.circuit_breaker.exception.circuit_breaker_open_exception import (
    CircuitBreakerOpenException,
)
from pycraftcore.circuit_breaker.port.async_circuit_breaker import AsyncCircuitBreaker
from pycraftcore.http.port.async_http_client import AsyncHttpClient
from pycraftcore.resilient_http.adapter.resilient_client import ResilientClient
from pycraftcore.retry.adapter.tenacity_retry_policy import TenacityRetryPolicy
from pycraftcore.retry.configuration.retry_configuration import RetrySettings
from pycraftcore.retry.port.retry import Retry
from pycraftcore.telemetry.adapter.null_telemetry import NullTelemetryTracer
from pycraftcore.telemetry.port.telemetry import TelemetryTracer


class FakeHttpClient(AsyncHttpClient):
    async def get(self, endpoint: str, *, params=None, headers=None) -> Any:
        return {"ok": True, "endpoint": endpoint}

    async def post(self, endpoint: str, *, body=None, headers=None) -> Any:
        return {"ok": True, "endpoint": endpoint, "body": body}


class FakeCircuitBreaker(AsyncCircuitBreaker):
    def __init__(self, settings: CircuitBreakerSettings | None = None) -> None:
        self._settings = settings or CircuitBreakerSettings()
        self.calls: list[Any] = []

    @property
    def settings(self) -> CircuitBreakerSettings:
        return self._settings

    @property
    def state(self) -> CircuitState:
        return CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        self.calls.append((func, args, kwargs))
        return await func(*args, **kwargs)


class FakeRetry(Retry):
    def __init__(self, settings: RetrySettings | None = None) -> None:
        self._settings = settings or RetrySettings()
        self.decorated: list[Any] = []

    @property
    def settings(self) -> RetrySettings:
        return self._settings

    def decorator(self, func):
        self.decorated.append(func)
        return func


class FakeTelemetry(TelemetryTracer):
    def __init__(self) -> None:
        self.traced_spans: list[tuple[str, dict[str, Any]]] = []

    def trace(self, span_name: str, static_attributes: dict[str, Any]):
        self.traced_spans.append((span_name, static_attributes))

        def decorator(func):
            return func

        return decorator


@pytest.fixture
def resilient_client():
    return ResilientClient(
        base_client=FakeHttpClient(),
        circuit_breaker=FakeCircuitBreaker(),
        retry_policy=FakeRetry(),
        trace_manager=FakeTelemetry(),
    )


@pytest.mark.asyncio
async def test_get_returns_response(resilient_client):
    result = await resilient_client.get(endpoint="/health")

    assert result == {"ok": True, "endpoint": "/health"}


@pytest.mark.asyncio
async def test_post_returns_response(resilient_client):
    result = await resilient_client.post(endpoint="/users", body={"name": "john"})

    assert result == {"ok": True, "endpoint": "/users", "body": {"name": "john"}}


@pytest.mark.asyncio
async def test_every_call_goes_through_the_circuit_breaker():
    breaker = FakeCircuitBreaker()
    client = ResilientClient(
        base_client=FakeHttpClient(),
        circuit_breaker=breaker,
        retry_policy=FakeRetry(),
        trace_manager=FakeTelemetry(),
    )

    await client.get(endpoint="/health")
    await client.post(endpoint="/health")

    assert len(breaker.calls) == 2


@pytest.mark.asyncio
async def test_retry_decorator_is_applied_once_per_method_at_construction():
    retry = FakeRetry()

    ResilientClient(
        base_client=FakeHttpClient(),
        circuit_breaker=FakeCircuitBreaker(),
        retry_policy=retry,
        trace_manager=FakeTelemetry(),
    )

    assert len(retry.decorated) == 2


@pytest.mark.asyncio
async def test_telemetry_trace_is_applied_once_per_method_with_span_attributes():
    telemetry = FakeTelemetry()
    retry_settings = RetrySettings(retry_count=2, retry_delay=1, max_retry_delay=4)
    breaker_settings = CircuitBreakerSettings(failure_threshold=5, recovery_timeout=15, name="svc")

    ResilientClient(
        base_client=FakeHttpClient(),
        circuit_breaker=FakeCircuitBreaker(breaker_settings),
        retry_policy=FakeRetry(retry_settings),
        trace_manager=telemetry,
    )

    assert len(telemetry.traced_spans) == 2
    span_names = {name for name, _ in telemetry.traced_spans}
    assert span_names == {"GET", "POST"}

    _, attributes = telemetry.traced_spans[0]
    assert attributes["retry.attempts"] == retry_settings.attempts
    assert attributes["retry.delay"] == 1
    assert attributes["retry.max_delay"] == 4
    assert attributes["circuit_breaker.name"] == "svc"
    assert attributes["circuit_breaker.failure_threshold"] == 5
    assert attributes["circuit_breaker.recovery_timeout"] == 15


@pytest.mark.asyncio
async def test_defaults_to_null_telemetry_tracer_when_none_provided():
    client = ResilientClient(
        base_client=FakeHttpClient(),
        circuit_breaker=FakeCircuitBreaker(),
        retry_policy=FakeRetry(),
    )

    assert isinstance(client._trace, NullTelemetryTracer)
    result = await client.get(endpoint="/health")
    assert result == {"ok": True, "endpoint": "/health"}


@pytest.mark.asyncio
async def test_circuit_breaker_property_exposes_the_configured_breaker():
    breaker = FakeCircuitBreaker()
    client = ResilientClient(
        base_client=FakeHttpClient(),
        circuit_breaker=breaker,
        retry_policy=FakeRetry(),
    )

    assert client.circuit_breaker is breaker


@pytest.mark.asyncio
async def test_exception_from_circuit_breaker_propagates():
    class RejectingCircuitBreaker(FakeCircuitBreaker):
        async def call(self, func, *args, **kwargs):
            raise CircuitBreakerOpenException("open")

    client = ResilientClient(
        base_client=FakeHttpClient(),
        circuit_breaker=RejectingCircuitBreaker(),
        retry_policy=FakeRetry(),
    )

    with pytest.raises(CircuitBreakerOpenException):
        await client.get(endpoint="/health")


@pytest.mark.asyncio
async def test_integration_real_retry_and_breaker_recover_after_transient_failures():
    # Full stack, no fakes: verifies the retry-inside-breaker composition
    # actually works end to end against a flaky backend.
    call_count = {"n": 0}

    class FlakyHttpClient(AsyncHttpClient):
        async def get(self, endpoint, *, params=None, headers=None):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ConnectionError("transient")
            return {"ok": True}

        async def post(self, endpoint, *, body=None, headers=None):
            raise NotImplementedError

    client = ResilientClient(
        base_client=FlakyHttpClient(),
        circuit_breaker=AioBreakerCircuitBreakerPolicy(
            CircuitBreakerSettings(failure_threshold=5, recovery_timeout=1)
        ),
        retry_policy=TenacityRetryPolicy(
            RetrySettings(retry_count=3, retry_delay=0.001, max_retry_delay=0.002, jitter=0.0)
        ),
    )

    result = await client.get(endpoint="/health")

    assert result == {"ok": True}
    assert call_count["n"] == 3
    assert client.circuit_breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_integration_circuit_breaker_short_circuits_after_exhausted_retries():
    class AlwaysFailingHttpClient(AsyncHttpClient):
        async def get(self, endpoint, *, params=None, headers=None):
            raise ConnectionError("down")

        async def post(self, endpoint, *, body=None, headers=None):
            raise NotImplementedError

    client = ResilientClient(
        base_client=AlwaysFailingHttpClient(),
        circuit_breaker=AioBreakerCircuitBreakerPolicy(
            CircuitBreakerSettings(failure_threshold=1, recovery_timeout=10)
        ),
        retry_policy=TenacityRetryPolicy(
            RetrySettings(retry_count=1, retry_delay=0.001, max_retry_delay=0.002, jitter=0.0)
        ),
    )

    with pytest.raises(ConnectionError):
        await client.get(endpoint="/health")

    assert client.circuit_breaker.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenException):
        await client.get(endpoint="/health")
