import pytest

from pycraftcore.retry.configuration.retry_configuration import RetrySettings


def test_defaults():
    settings = RetrySettings()

    assert settings.retry_count == 4
    assert settings.retry_delay == 5
    assert settings.retry_on == (Exception,)
    assert settings.max_retry_delay == 8.0
    assert settings.jitter == 0.5
    assert settings.should_retry is None


def test_attempts_is_retry_count_plus_one():
    assert RetrySettings(retry_count=0).attempts == 1
    assert RetrySettings(retry_count=4).attempts == 5


def test_rejects_negative_retry_count():
    with pytest.raises(ValueError, match="retry_count must be greater than or equal to 0"):
        RetrySettings(retry_count=-1)


def test_accepts_zero_retry_count():
    settings = RetrySettings(retry_count=0)

    assert settings.attempts == 1


def test_rejects_non_positive_retry_delay():
    with pytest.raises(ValueError, match="retry_delay must be greater than 0"):
        RetrySettings(retry_delay=0)


def test_rejects_max_retry_delay_below_retry_delay():
    with pytest.raises(
        ValueError, match="max_retry_delay must be greater than or equal to retry_delay"
    ):
        RetrySettings(retry_delay=5, max_retry_delay=1)


def test_accepts_max_retry_delay_equal_to_retry_delay():
    settings = RetrySettings(retry_delay=5, max_retry_delay=5)

    assert settings.max_retry_delay == 5


def test_rejects_negative_jitter():
    with pytest.raises(ValueError, match="jitter must be greater than or equal to 0"):
        RetrySettings(jitter=-0.1)


def test_rejects_empty_retry_on_when_should_retry_not_provided():
    with pytest.raises(
        ValueError, match="retry_on cannot be empty when should_retry is not provided"
    ):
        RetrySettings(retry_on=())


def test_allows_empty_retry_on_when_should_retry_provided():
    settings = RetrySettings(retry_on=(), should_retry=lambda exc: True)

    assert settings.retry_on == ()
    assert settings.should_retry is not None
