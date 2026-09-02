from unittest.mock import AsyncMock, MagicMock

import pytest

from pycraftcore.retry.adapter.tenacity_retry_policy import TenacityRetryPolicy
from pycraftcore.retry.configuration.retry_configuration import RetrySettings

FAST = {"retry_delay": 0.001, "max_retry_delay": 0.002, "jitter": 0.0}


@pytest.mark.asyncio
async def test_succeeds_on_first_try_without_retrying():
    settings = RetrySettings(retry_count=3, retry_on=(Exception,), **FAST)
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(return_value="ok")
    wrapped = policy.decorator(mock_func)

    result = await wrapped()

    assert result == "ok"
    mock_func.assert_awaited_once()


@pytest.mark.asyncio
async def test_retries_until_eventual_success():
    settings = RetrySettings(retry_count=3, retry_on=(ValueError,), **FAST)
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(side_effect=[ValueError("fail"), ValueError("fail again"), "success"])
    wrapped = policy.decorator(mock_func)

    result = await wrapped()

    assert result == "success"
    assert mock_func.await_count == 3


@pytest.mark.asyncio
async def test_reraises_original_exception_after_exhausting_attempts():
    settings = RetrySettings(retry_count=2, retry_on=(Exception,), **FAST)
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(side_effect=ValueError("boom"))
    wrapped = policy.decorator(mock_func)

    with pytest.raises(ValueError, match="boom"):
        await wrapped()

    # attempts = retry_count + 1
    assert mock_func.await_count == 3


@pytest.mark.asyncio
async def test_does_not_retry_exception_outside_retry_on():
    settings = RetrySettings(retry_count=3, retry_on=(ValueError,), **FAST)
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(side_effect=KeyError("stop"))
    wrapped = policy.decorator(mock_func)

    with pytest.raises(KeyError):
        await wrapped()

    mock_func.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_retry_predicate_overrides_retry_on():
    settings = RetrySettings(
        retry_count=2,
        retry_on=(ValueError,),
        should_retry=lambda exc: isinstance(exc, KeyError),
        **FAST,
    )
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(side_effect=[KeyError("retry me"), "ok"])
    wrapped = policy.decorator(mock_func)

    result = await wrapped()

    assert result == "ok"
    assert mock_func.await_count == 2


@pytest.mark.asyncio
async def test_should_retry_predicate_can_reject_types_in_retry_on():
    settings = RetrySettings(
        retry_count=3,
        retry_on=(ValueError,),
        should_retry=lambda exc: False,
        **FAST,
    )
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(side_effect=ValueError("not retried"))
    wrapped = policy.decorator(mock_func)

    with pytest.raises(ValueError):
        await wrapped()

    mock_func.assert_awaited_once()


@pytest.mark.asyncio
async def test_zero_retries_fails_after_a_single_attempt():
    settings = RetrySettings(retry_count=0, retry_on=(ValueError,), **FAST)
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(side_effect=ValueError("fail"))
    wrapped = policy.decorator(mock_func)

    with pytest.raises(ValueError):
        await wrapped()

    mock_func.assert_awaited_once()


@pytest.mark.asyncio
async def test_preserves_call_arguments():
    settings = RetrySettings(retry_count=1, retry_on=(Exception,), **FAST)
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(return_value="ok")
    wrapped = policy.decorator(mock_func)

    await wrapped(1, 2, key="value")

    mock_func.assert_awaited_once_with(1, 2, key="value")


@pytest.mark.asyncio
async def test_each_call_gets_independent_retry_state():
    # tenacity's `.wraps()` must copy state per invocation; concurrent/sequential
    # calls to the same wrapped callable must not share attempt counters.
    settings = RetrySettings(retry_count=2, retry_on=(ValueError,), **FAST)
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(side_effect=[ValueError("a"), "first-ok", ValueError("b"), "second-ok"])
    wrapped = policy.decorator(mock_func)

    first = await wrapped()
    second = await wrapped()

    assert first == "first-ok"
    assert second == "second-ok"
    assert mock_func.await_count == 4


@pytest.mark.asyncio
async def test_logs_each_retry_attempt():
    settings = RetrySettings(retry_count=2, retry_on=(ValueError,), **FAST)
    logger = MagicMock()
    policy = TenacityRetryPolicy(settings, logger=logger)

    mock_func = AsyncMock(side_effect=[ValueError("fail"), "ok"])
    wrapped = policy.decorator(mock_func)

    await wrapped()

    logger.warning.assert_called_once()
    message = logger.warning.call_args[0][0]
    assert "Attempt 1/3 failed" in message


@pytest.mark.asyncio
async def test_does_not_log_when_no_logger_provided():
    settings = RetrySettings(retry_count=2, retry_on=(ValueError,), **FAST)
    policy = TenacityRetryPolicy(settings)

    mock_func = AsyncMock(side_effect=[ValueError("fail"), "ok"])
    wrapped = policy.decorator(mock_func)

    await wrapped()  # must not raise


def test_settings_property_returns_configured_settings():
    settings = RetrySettings()
    policy = TenacityRetryPolicy(settings)

    assert policy.settings is settings


def test_defaults_settings_when_none_provided():
    policy = TenacityRetryPolicy()

    assert isinstance(policy.settings, RetrySettings)
