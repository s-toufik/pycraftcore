from typing import Any

import httpx
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
from pycraftcore.http.policy.http_error_policy import is_business_error, is_retryable
from pycraftcore.resilient_http.adapter.resilient_transport import (
    ResilientTransport,
    TransportStatusError,
)
from pycraftcore.retry.adapter.tenacity_retry_policy import TenacityRetryPolicy
from pycraftcore.retry.configuration.retry_configuration import RetrySettings
from pycraftcore.retry.port.retry import Retry

FAST_RETRY = RetrySettings(
    retry_count=3, retry_delay=0.001, max_retry_delay=0.002, jitter=0.0, should_retry=is_retryable
)


class ScriptedTransport(httpx.AsyncBaseTransport):
    """A fake wrapped transport that plays back a scripted sequence of responses/exceptions."""

    def __init__(self, script: list[httpx.Response | BaseException]) -> None:
        self._script = list(script)
        self.requests: list[httpx.Request] = []
        self.closed = False

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        item = self._script.pop(0)
        if isinstance(item, BaseException):
            raise item
        item.request = request
        return item

    async def aclose(self) -> None:
        self.closed = True


class FakeCircuitBreaker(AsyncCircuitBreaker):
    def __init__(self, settings: CircuitBreakerSettings | None = None) -> None:
        self._settings = settings or CircuitBreakerSettings()

    @property
    def settings(self) -> CircuitBreakerSettings:
        return self._settings

    @property
    def state(self) -> CircuitState:
        return CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        return await func(*args, **kwargs)


class RejectingCircuitBreaker(FakeCircuitBreaker):
    async def call(self, func, *args, **kwargs):
        raise CircuitBreakerOpenException("open")


class FakeRetry(Retry):
    def __init__(self, settings: RetrySettings | None = None) -> None:
        self._settings = settings or RetrySettings(should_retry=lambda exc: False)

    @property
    def settings(self) -> RetrySettings:
        return self._settings

    def decorator(self, func):
        return func  # passthrough: no retrying


def make_request(method: str = "GET", json: dict[str, Any] | None = None) -> httpx.Request:
    return httpx.Request(method, "https://api.test.com/health", json=json)


@pytest.mark.asyncio
async def test_successful_response_passes_through_untouched():
    wrapped = ScriptedTransport([httpx.Response(200, json={"ok": True})])
    transport = ResilientTransport(
        transport=wrapped, circuit_breaker=FakeCircuitBreaker(), retry_policy=FakeRetry()
    )

    response = await transport.handle_async_request(make_request())

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert len(wrapped.requests) == 1


@pytest.mark.asyncio
async def test_error_response_is_returned_not_raised():
    # The transport contract: HTTP-level errors come back as a Response,
    # never as a raised exception -- that's what response.raise_for_status()
    # is for, at a layer above the transport.
    wrapped = ScriptedTransport([httpx.Response(404, json={"error": "missing"})])
    transport = ResilientTransport(
        transport=wrapped, circuit_breaker=FakeCircuitBreaker(), retry_policy=FakeRetry()
    )

    response = await transport.handle_async_request(make_request())

    assert response.status_code == 404
    assert response.json() == {"error": "missing"}


class TrackingByteStream(httpx.AsyncByteStream):
    """A response body stream that records whether it was actually iterated,
    so tests can prove the transport drained it rather than just trusting
    that Response(json=...) is already pre-materialized."""

    def __init__(self, content: bytes) -> None:
        self._content = content
        self.iterated = False

    async def __aiter__(self):
        self.iterated = True
        yield self._content


@pytest.mark.asyncio
async def test_error_response_body_is_drained_before_being_returned():
    # Draining before returning matters for HTTP/1.1 keep-alive: the pool
    # must not reuse a connection with an unread response still on the wire.
    stream = TrackingByteStream(b'{"error": "boom"}')
    error_response = httpx.Response(
        500, headers={"content-type": "application/json"}, stream=stream
    )

    wrapped = ScriptedTransport([error_response])
    transport = ResilientTransport(
        transport=wrapped, circuit_breaker=FakeCircuitBreaker(), retry_policy=FakeRetry()
    )

    response = await transport.handle_async_request(make_request())

    assert stream.iterated is True
    assert response.status_code == 500
    assert response.json() == {"error": "boom"}


@pytest.mark.asyncio
async def test_successful_streaming_response_body_is_not_eagerly_drained():
    # Critical for SSE/token streaming (e.g. LLM chat completions): a 200
    # response must pass through with its body stream untouched so the
    # caller can iterate it lazily instead of getting it pre-buffered.
    stream = TrackingByteStream(b"data: token\n\n")
    success_response = httpx.Response(200, stream=stream)

    wrapped = ScriptedTransport([success_response])
    transport = ResilientTransport(
        transport=wrapped, circuit_breaker=FakeCircuitBreaker(), retry_policy=FakeRetry()
    )

    response = await transport.handle_async_request(make_request())

    assert stream.iterated is False
    assert response.status_code == 200

    chunks = [chunk async for chunk in response.aiter_bytes()]
    assert chunks == [b"data: token\n\n"]
    assert stream.iterated is True


@pytest.mark.asyncio
async def test_retries_transient_failure_and_returns_eventual_success():
    wrapped = ScriptedTransport(
        [
            httpx.Response(500, json={}),
            httpx.Response(500, json={}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = ResilientTransport(
        transport=wrapped,
        circuit_breaker=FakeCircuitBreaker(),
        retry_policy=TenacityRetryPolicy(FAST_RETRY),
    )

    response = await transport.handle_async_request(make_request())

    assert response.status_code == 200
    assert len(wrapped.requests) == 3


@pytest.mark.asyncio
async def test_retries_exhausted_returns_final_error_response_not_raised():
    wrapped = ScriptedTransport([httpx.Response(500, json={})] * 4)
    transport = ResilientTransport(
        transport=wrapped,
        circuit_breaker=FakeCircuitBreaker(),
        retry_policy=TenacityRetryPolicy(
            RetrySettings(
                retry_count=3,
                retry_delay=0.001,
                max_retry_delay=0.002,
                jitter=0.0,
                should_retry=is_retryable,
            )
        ),
    )

    response = await transport.handle_async_request(make_request())

    assert response.status_code == 500
    assert len(wrapped.requests) == 4


@pytest.mark.asyncio
async def test_business_error_is_not_retried():
    wrapped = ScriptedTransport([httpx.Response(422, json={"error": "invalid"})])
    transport = ResilientTransport(
        transport=wrapped,
        circuit_breaker=FakeCircuitBreaker(),
        retry_policy=TenacityRetryPolicy(FAST_RETRY),
    )

    response = await transport.handle_async_request(make_request())

    assert response.status_code == 422
    assert len(wrapped.requests) == 1


@pytest.mark.asyncio
async def test_request_body_is_replayed_identically_across_retries():
    wrapped = ScriptedTransport(
        [
            httpx.Response(500, json={}),
            httpx.Response(500, json={}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = ResilientTransport(
        transport=wrapped,
        circuit_breaker=FakeCircuitBreaker(),
        retry_policy=TenacityRetryPolicy(FAST_RETRY),
    )

    await transport.handle_async_request(make_request("POST", json={"messages": ["hi"]}))

    bodies = [req.read() for req in wrapped.requests]
    assert bodies == [b'{"messages":["hi"]}'] * 3


@pytest.mark.asyncio
async def test_circuit_breaker_open_exception_propagates_uncaught():
    wrapped = ScriptedTransport([httpx.Response(200, json={"ok": True})])
    transport = ResilientTransport(
        transport=wrapped, circuit_breaker=RejectingCircuitBreaker(), retry_policy=FakeRetry()
    )

    with pytest.raises(CircuitBreakerOpenException):
        await transport.handle_async_request(make_request())

    assert len(wrapped.requests) == 0


@pytest.mark.asyncio
async def test_non_status_transport_exception_propagates_uncaught():
    wrapped = ScriptedTransport([httpx.ConnectError("refused")])
    transport = ResilientTransport(
        transport=wrapped, circuit_breaker=FakeCircuitBreaker(), retry_policy=FakeRetry()
    )

    with pytest.raises(httpx.ConnectError):
        await transport.handle_async_request(make_request())


@pytest.mark.asyncio
async def test_aclose_delegates_to_wrapped_transport():
    wrapped = ScriptedTransport([])
    transport = ResilientTransport(
        transport=wrapped, circuit_breaker=FakeCircuitBreaker(), retry_policy=FakeRetry()
    )

    await transport.aclose()

    assert wrapped.closed is True


@pytest.mark.asyncio
async def test_integration_real_breaker_opens_after_exhausted_retries():
    wrapped = ScriptedTransport([httpx.Response(500, json={})] * 2)
    transport = ResilientTransport(
        transport=wrapped,
        circuit_breaker=AioBreakerCircuitBreakerPolicy(
            CircuitBreakerSettings(
                failure_threshold=1, recovery_timeout=10, is_excluded=is_business_error
            )
        ),
        retry_policy=TenacityRetryPolicy(
            RetrySettings(
                retry_count=1,
                retry_delay=0.001,
                max_retry_delay=0.002,
                jitter=0.0,
                should_retry=is_retryable,
            )
        ),
    )

    response = await transport.handle_async_request(make_request())
    assert response.status_code == 500

    with pytest.raises(CircuitBreakerOpenException):
        await transport.handle_async_request(make_request())


def test_transport_status_error_message_includes_status_and_url():
    request = make_request()
    response = httpx.Response(503, request=request)

    error = TransportStatusError(request, response)

    assert "503" in str(error)
    assert "api.test.com" in str(error)
    assert error.response is response
    assert error.request is request
