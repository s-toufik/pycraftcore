import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from pycraftcore.http.adapter import CircuitBreakerPolicy
from pycraftcore.http.configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.http.enum import CircuitState
from pycraftcore.http.exception.circuit_breaker_open_exception import (
    CircuitBreakerOpenException,
)


@pytest.mark.asyncio
async def test_circuit_breaker_success_keeps_closed():
    policy = CircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=2))

    mock_func = AsyncMock(return_value="ok")

    result = await policy.call(mock_func)

    assert result == "ok"
    assert policy.state == CircuitState.CLOSED
    assert policy._failure_counter == 0


@pytest.mark.asyncio
async def test_circuit_breaker_failure_increments_counter():
    policy = CircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=2))

    mock_func = AsyncMock(side_effect=ValueError("fail"))

    with pytest.raises(ValueError):
        await policy.call(mock_func)

    assert policy._failure_counter == 1
    assert policy.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    policy = CircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=2))

    mock_func = AsyncMock(side_effect=ValueError("fail"))

    with pytest.raises(ValueError):
        await policy.call(mock_func)

    with pytest.raises(ValueError):
        await policy.call(mock_func)

    assert policy.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_blocks_when_open():
    policy = CircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=1))

    mock_func = AsyncMock(side_effect=ValueError("fail"))

    with pytest.raises(ValueError):
        await policy.call(mock_func)

    assert policy.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenException):
        await policy.call(mock_func)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_after_timeout():

    settings = CircuitBreakerSettings(
        failure_threshold=1,
        recovery_timeout=10,
    )

    policy = CircuitBreakerPolicy(settings)
    policy._clock = lambda: 1000
    mock_func = AsyncMock(side_effect=ValueError("fail"))
    with pytest.raises(ValueError):
        await policy.call(mock_func)

    assert policy.state.name == "OPEN"
    policy._clock = lambda: 1011

    assert policy._can_attempt() is True


@pytest.mark.asyncio
async def test_circuit_breaker_recovery_to_closed():
    settings = CircuitBreakerSettings(failure_threshold=1, success_threshold=2, recovery_timeout=10)

    policy = CircuitBreakerPolicy(settings)

    fail = AsyncMock(side_effect=ValueError("fail"))
    success = AsyncMock(return_value="ok")

    # trip circuit open
    with pytest.raises(ValueError):
        await policy.call(fail)

    # force HALF_OPEN
    with patch("time.time", return_value=1000):
        policy._state = CircuitState.HALF_OPEN

        await policy.call(success)
        await policy.call(success)

    assert policy.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_recovery_allows_call():

    settings = CircuitBreakerSettings(
        failure_threshold=1,
        recovery_timeout=10,
    )

    policy = CircuitBreakerPolicy(settings)
    policy._clock = lambda: 1000

    fail_func = AsyncMock(side_effect=ValueError("fail"))

    with pytest.raises(ValueError):
        await policy.call(fail_func)

    assert policy.state.name == "OPEN"

    policy._clock = lambda: 1011
    success_func = AsyncMock(return_value="ok")
    result = await policy.call(success_func)

    assert result == "ok"
    assert policy.state.name in {"HALF_OPEN", "CLOSED"}


@pytest.mark.asyncio
async def test_lock_prevents_double_half_open_transition():
    settings = CircuitBreakerSettings(
        failure_threshold=1,
        success_threshold=2,
        recovery_timeout=0,  # recovers immediately
    )
    cb = CircuitBreakerPolicy(settings=settings)

    # Trip the breaker
    with pytest.raises(Exception):
        await cb.call(AsyncMock(side_effect=Exception("boom")))

    assert cb._state == CircuitState.OPEN

    probe_entry_count = 0

    async def counting_probe():
        nonlocal probe_entry_count
        probe_entry_count += 1
        await asyncio.sleep(0)
        return "ok"

    await asyncio.gather(
        cb.call(counting_probe),
        cb.call(counting_probe),
        return_exceptions=True,
    )

    assert probe_entry_count == 2
    assert cb._state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_half_open_failure_reopens_circuit_immediately_even_below_threshold():
    settings = CircuitBreakerSettings(failure_threshold=5, recovery_timeout=10)
    policy = CircuitBreakerPolicy(settings)
    policy._clock = lambda: 1000

    with pytest.raises(ValueError):
        await policy.call(AsyncMock(side_effect=ValueError("fail")))

    policy._state = CircuitState.HALF_OPEN
    policy._success_counter = 1

    with pytest.raises(ValueError):
        await policy.call(AsyncMock(side_effect=ValueError("probe failed")))

    assert policy.state == CircuitState.OPEN
    assert policy._success_counter == 0
    assert policy._failure_counter < settings.failure_threshold


@pytest.mark.asyncio
async def test_can_attempt_at_exact_recovery_timeout_boundary():
    settings = CircuitBreakerSettings(failure_threshold=1, recovery_timeout=10)
    policy = CircuitBreakerPolicy(settings)
    policy._clock = lambda: 1000

    with pytest.raises(ValueError):
        await policy.call(AsyncMock(side_effect=ValueError("fail")))

    policy._clock = lambda: 1010

    assert policy._can_attempt() is True


def test_settings_property_returns_configured_settings():
    settings = CircuitBreakerSettings(failure_threshold=5)
    policy = CircuitBreakerPolicy(settings)

    assert policy.settings is settings


def test_defaults_settings_when_none_provided():
    policy = CircuitBreakerPolicy()

    assert isinstance(policy.settings, CircuitBreakerSettings)


def test_last_exception_is_none_before_any_failure():
    policy = CircuitBreakerPolicy()

    assert policy.last_exception is None


@pytest.mark.asyncio
async def test_last_exception_is_set_after_failure():
    policy = CircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=2))

    with pytest.raises(ValueError):
        await policy.call(AsyncMock(side_effect=ValueError("boom")))

    assert isinstance(policy.last_exception, ValueError)
