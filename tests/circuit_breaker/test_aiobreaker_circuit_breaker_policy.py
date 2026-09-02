import asyncio
from unittest.mock import MagicMock

import pytest
from aiobreaker import CircuitBreakerState

from pycraftcore.circuit_breaker.adapter.aiobreaker_circuit_breaker_policy import (
    AioBreakerCircuitBreakerPolicy,
    CircuitBreakerLogger,
)
from pycraftcore.circuit_breaker.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.circuit_breaker.enum.circuit_breaker_status import CircuitState
from pycraftcore.circuit_breaker.exception.circuit_breaker_open_exception import (
    CircuitBreakerOpenException,
)

# NOTE: `func` must be a plain coroutine function, not unittest.mock.AsyncMock.
# aiobreaker's CircuitBreaker.call_async() special-cases any callable whose
# `_ignore_on_call` attribute is truthy (its own @breaker-decorator marker) and
# bypasses the breaker entirely -- and AsyncMock auto-vivifies that attribute
# as a truthy child mock, so a bare AsyncMock silently skips the breaker.


def ok(value="ok"):
    async def _call(*args, **kwargs):
        return value

    return _call


def failing(exception):
    async def _call(*args, **kwargs):
        raise exception

    return _call


@pytest.mark.asyncio
async def test_success_keeps_circuit_closed():
    policy = AioBreakerCircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=2))

    result = await policy.call(ok())

    assert result == "ok"
    assert policy.state == CircuitState.CLOSED
    assert policy.failure_count == 0


@pytest.mark.asyncio
async def test_failure_below_threshold_keeps_circuit_closed():
    policy = AioBreakerCircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=3))

    with pytest.raises(ValueError):
        await policy.call(failing(ValueError("fail")))

    assert policy.state == CircuitState.CLOSED
    assert policy.failure_count == 1


@pytest.mark.asyncio
async def test_success_resets_the_failure_counter():
    policy = AioBreakerCircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=3))

    with pytest.raises(ValueError):
        await policy.call(failing(ValueError("fail")))
    assert policy.failure_count == 1

    result = await policy.call(ok())

    assert result == "ok"
    assert policy.state == CircuitState.CLOSED
    assert policy.failure_count == 0


@pytest.mark.asyncio
async def test_call_that_trips_the_breaker_raises_the_original_exception():
    # The failure that crosses the threshold surfaces as itself, not as
    # CircuitBreakerOpenException -- only calls rejected by an already-open
    # breaker get translated.
    policy = AioBreakerCircuitBreakerPolicy(CircuitBreakerSettings(failure_threshold=1))

    with pytest.raises(ValueError, match="boom"):
        await policy.call(failing(ValueError("boom")))

    assert policy.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_call_while_open_is_rejected_with_circuit_breaker_open_exception():
    policy = AioBreakerCircuitBreakerPolicy(
        CircuitBreakerSettings(failure_threshold=1, recovery_timeout=10)
    )

    with pytest.raises(ValueError):
        await policy.call(failing(ValueError("boom")))

    assert policy.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenException):
        await policy.call(ok("should not run"))


@pytest.mark.asyncio
async def test_half_open_probe_success_closes_the_circuit():
    policy = AioBreakerCircuitBreakerPolicy(
        CircuitBreakerSettings(failure_threshold=1, recovery_timeout=0.02)
    )

    with pytest.raises(ValueError):
        await policy.call(failing(ValueError("first")))
    assert policy.state == CircuitState.OPEN

    await asyncio.sleep(0.03)

    result = await policy.call(ok())

    assert result == "ok"
    assert policy.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_half_open_probe_failure_reopens_the_circuit():
    policy = AioBreakerCircuitBreakerPolicy(
        CircuitBreakerSettings(failure_threshold=1, recovery_timeout=0.02)
    )

    with pytest.raises(ValueError):
        await policy.call(failing(ValueError("first")))
    assert policy.state == CircuitState.OPEN

    await asyncio.sleep(0.03)

    with pytest.raises(ValueError, match="probe failed"):
        await policy.call(failing(ValueError("probe failed")))

    assert policy.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_probe_lock_serializes_calls_while_not_closed():
    # A burst of concurrent callers hitting a just-recovered breaker must be
    # serialized -- at most one call may be in flight at a time -- instead of
    # all being let through as simultaneous "trial" calls.
    policy = AioBreakerCircuitBreakerPolicy(
        CircuitBreakerSettings(failure_threshold=1, recovery_timeout=0.02)
    )

    with pytest.raises(ValueError):
        await policy.call(failing(ValueError("trip")))
    assert policy.state == CircuitState.OPEN

    await asyncio.sleep(0.03)

    in_flight = 0
    max_in_flight = 0

    async def probe(*args, **kwargs):
        nonlocal in_flight, max_in_flight
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
        await asyncio.sleep(0.02)
        in_flight -= 1
        return "ok"

    results = await asyncio.gather(policy.call(probe), policy.call(probe), policy.call(probe))

    assert max_in_flight == 1
    assert results == ["ok", "ok", "ok"]
    assert policy.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_excluded_exception_type_does_not_count_as_failure():
    policy = AioBreakerCircuitBreakerPolicy(
        CircuitBreakerSettings(failure_threshold=1, excluded_exceptions=(KeyError,))
    )

    with pytest.raises(KeyError):
        await policy.call(failing(KeyError("business error")))

    assert policy.state == CircuitState.CLOSED
    assert policy.failure_count == 0


@pytest.mark.asyncio
async def test_is_excluded_predicate_does_not_count_as_failure():
    policy = AioBreakerCircuitBreakerPolicy(
        CircuitBreakerSettings(failure_threshold=1, is_excluded=lambda exc: "skip" in str(exc))
    )

    with pytest.raises(ValueError, match="skip me"):
        await policy.call(failing(ValueError("skip me")))

    assert policy.state == CircuitState.CLOSED
    assert policy.failure_count == 0


@pytest.mark.asyncio
async def test_is_excluded_predicate_still_counts_non_matching_exceptions():
    policy = AioBreakerCircuitBreakerPolicy(
        CircuitBreakerSettings(failure_threshold=1, is_excluded=lambda exc: "skip" in str(exc))
    )

    with pytest.raises(ValueError, match="real failure"):
        await policy.call(failing(ValueError("real failure")))

    assert policy.state == CircuitState.OPEN


def test_settings_property_returns_configured_settings():
    settings = CircuitBreakerSettings(failure_threshold=5)
    policy = AioBreakerCircuitBreakerPolicy(settings)

    assert policy.settings is settings


def test_defaults_settings_when_none_provided():
    policy = AioBreakerCircuitBreakerPolicy()

    assert isinstance(policy.settings, CircuitBreakerSettings)
    assert policy.state == CircuitState.CLOSED


class TestCircuitBreakerLogger:
    def test_failure_logs_warning_with_counts(self):
        logger = MagicMock()
        cb_logger = CircuitBreakerLogger(CircuitBreakerSettings(name="svc"), logger)
        breaker = MagicMock(fail_counter=2, fail_max=3)

        cb_logger.failure(breaker, ValueError("boom"))

        logger.warning.assert_called_once()
        assert "svc" in logger.warning.call_args[0][0]

    def test_failure_does_nothing_without_logger(self):
        cb_logger = CircuitBreakerLogger(CircuitBreakerSettings())

        cb_logger.failure(MagicMock(), ValueError("boom"))  # must not raise

    def test_success_is_a_no_op(self):
        cb_logger = CircuitBreakerLogger(CircuitBreakerSettings())

        assert cb_logger.success(MagicMock()) is None

    def test_state_change_logs_info(self):
        logger = MagicMock()
        cb_logger = CircuitBreakerLogger(CircuitBreakerSettings(name="svc"), logger)
        breaker = MagicMock(fail_max=3)

        cb_logger.state_change(
            breaker,
            MagicMock(state=CircuitBreakerState.CLOSED),
            MagicMock(state=CircuitBreakerState.HALF_OPEN),
        )

        logger.info.assert_called_once()
        logger.error.assert_not_called()

    def test_state_change_logs_error_when_opening(self):
        logger = MagicMock()
        cb_logger = CircuitBreakerLogger(
            CircuitBreakerSettings(name="svc", recovery_timeout=30), logger
        )
        breaker = MagicMock(fail_max=3)

        cb_logger.state_change(
            breaker,
            MagicMock(state=CircuitBreakerState.CLOSED),
            MagicMock(state=CircuitBreakerState.OPEN),
        )

        logger.error.assert_called_once()

    def test_state_change_does_nothing_without_logger(self):
        cb_logger = CircuitBreakerLogger(CircuitBreakerSettings())

        cb_logger.state_change(MagicMock(), MagicMock(), MagicMock())  # must not raise
