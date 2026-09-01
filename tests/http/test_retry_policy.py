from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pycraftcore.http.adapter.retry_policy import RetryPolicy
from pycraftcore.http.configuration.retry_configuration import RetrySettings


@pytest.mark.asyncio
async def test_retry_policy_success_first_try():
    settings = RetrySettings(retry_count=3, retry_delay=0.1, retry_on=(Exception,))
    policy = RetryPolicy(settings)

    mock_func = AsyncMock(return_value="ok")
    wrapped = policy.decorator(mock_func)
    result = await wrapped()

    assert result == "ok"
    mock_func.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_policy_eventual_success():
    settings = RetrySettings(retry_count=3, retry_delay=0.1, retry_on=(ValueError,))
    policy = RetryPolicy(settings)

    mock_func = AsyncMock(side_effect=[ValueError("fail"), ValueError("fail again"), "success"])

    wrapped = policy.decorator(mock_func)
    with patch("asyncio.sleep", new=AsyncMock()) as sleep_mock:
        result = await wrapped()

    assert result == "success"
    assert mock_func.await_count == 3
    assert sleep_mock.await_count == 2


@pytest.mark.asyncio
async def test_retry_policy_exponential_backoff():
    settings = RetrySettings(retry_count=3, retry_delay=1.0, retry_on=(Exception,))
    policy = RetryPolicy(settings)

    mock_func = AsyncMock(side_effect=[Exception("fail"), Exception("fail"), "ok"])
    wrapped = policy.decorator(mock_func)
    sleep_calls = []

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    with patch("asyncio.sleep", new=fake_sleep):
        result = await wrapped()

    assert result == "ok"
    assert sleep_calls == [1.0, 2.0]


@pytest.mark.asyncio
async def test_retry_policy_fails_after_retries():
    settings = RetrySettings(retry_count=2, retry_delay=0.1, retry_on=(Exception,))
    policy = RetryPolicy(settings)

    mock_func = AsyncMock(side_effect=Exception("boom"))
    wrapped = policy.decorator(mock_func)

    with (
        patch("asyncio.sleep", new=AsyncMock()),
        pytest.raises(Exception, match="boom"),
    ):
        await wrapped()

    assert mock_func.await_count == 3


@pytest.mark.asyncio
async def test_retry_policy_does_not_retry_unhandled_exception():
    settings = RetrySettings(retry_count=3, retry_delay=0.1, retry_on=(ValueError,))
    policy = RetryPolicy(settings)

    mock_func = AsyncMock(side_effect=KeyError("stop"))
    wrapped = policy.decorator(mock_func)
    with patch("asyncio.sleep", new=AsyncMock()), pytest.raises(KeyError):
        await wrapped()

    assert mock_func.await_count == 1


@pytest.mark.asyncio
async def test_retry_policy_preserves_arguments():
    settings = RetrySettings(retry_count=2, retry_delay=0.1, retry_on=(Exception,))
    policy = RetryPolicy(settings)

    mock_func = AsyncMock(return_value="ok")
    wrapped = policy.decorator(mock_func)
    await wrapped(1, 2, key="value")

    mock_func.assert_awaited_once_with(1, 2, key="value")


@pytest.mark.asyncio
async def test_retry_policy_empty_retry_on_raises():
    with pytest.raises(RuntimeError, match="retry_on cannot be empty"):
        RetrySettings(retry_count=3, retry_delay=0.1, retry_on=())


@pytest.mark.asyncio
async def test_retry_policy_zero_retries_failure():
    settings = RetrySettings(retry_count=0, retry_delay=0.1, retry_on=(Exception,))

    policy = RetryPolicy(settings)
    mock_func = AsyncMock(side_effect=ValueError("fail"))
    wrapped = policy.decorator(mock_func)

    with pytest.raises(ValueError):
        await wrapped()

    mock_func.assert_awaited_once()


def test_retry_policy_exposes_settings():
    settings = RetrySettings(retry_count=2, retry_delay=0.1, retry_on=(Exception,))
    policy = RetryPolicy(settings)

    assert policy.settings is settings


def test_retry_policy_defaults_settings_when_none_provided():
    policy = RetryPolicy()

    assert isinstance(policy.settings, RetrySettings)


@pytest.mark.asyncio
async def test_retry_policy_logs_each_retry_attempt():
    settings = RetrySettings(retry_count=2, retry_delay=0.1, retry_on=(ValueError,))
    logger = MagicMock()
    policy = RetryPolicy(settings, logger=logger)

    mock_func = AsyncMock(side_effect=[ValueError("fail"), "ok"])
    wrapped = policy.decorator(mock_func)

    with patch("asyncio.sleep", new=AsyncMock()):
        await wrapped()

    logger.warning.assert_called_once()
