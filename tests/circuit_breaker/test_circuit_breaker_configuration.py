import pytest

from pycraftcore.circuit_breaker.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)


def test_defaults():
    settings = CircuitBreakerSettings()

    assert settings.failure_threshold == 3
    assert settings.recovery_timeout == 5.0
    assert settings.excluded_exceptions == ()
    assert settings.is_excluded is None
    assert settings.name == "default"


def test_rejects_failure_threshold_below_one():
    with pytest.raises(ValueError, match="failure_threshold must be greater than or equal to 1"):
        CircuitBreakerSettings(failure_threshold=0)


def test_accepts_failure_threshold_of_one():
    settings = CircuitBreakerSettings(failure_threshold=1)

    assert settings.failure_threshold == 1


def test_rejects_non_positive_recovery_timeout():
    with pytest.raises(ValueError, match="recovery_timeout must be greater than 0"):
        CircuitBreakerSettings(recovery_timeout=0)
