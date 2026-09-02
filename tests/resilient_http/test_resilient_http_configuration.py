from pycraftcore.circuit_breaker.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.http.configuration import HttpClientSettings
from pycraftcore.http.policy.http_error_policy import is_business_error, is_retryable
from pycraftcore.resilient_http.configuration.resilient_http_configuration import (
    ResilientHttpSettings,
)
from pycraftcore.retry.configuration.retry_configuration import RetrySettings


def test_builds_all_sub_settings_with_defaults():
    settings = ResilientHttpSettings()

    assert isinstance(settings.http, HttpClientSettings)
    assert isinstance(settings.retry, RetrySettings)
    assert isinstance(settings.circuit_breaker, CircuitBreakerSettings)


def test_default_retry_settings_classify_transient_http_failures():
    settings = ResilientHttpSettings()

    assert settings.retry.should_retry is is_retryable


def test_default_circuit_breaker_settings_exclude_business_errors():
    settings = ResilientHttpSettings()

    assert settings.circuit_breaker.is_excluded is is_business_error
    assert settings.circuit_breaker.name == "http"


def test_sub_settings_are_independent_instances():
    first = ResilientHttpSettings()
    second = ResilientHttpSettings()

    assert first.http is not second.http
    assert first.retry is not second.retry
    assert first.circuit_breaker is not second.circuit_breaker
