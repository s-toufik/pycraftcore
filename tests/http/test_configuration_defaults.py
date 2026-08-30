import pytest

from pycraftcore.http.configuration import (
    CircuitBreakerSettings,
    ClientSettings,
    HttpClientSettings,
    LimitsSettings,
    RetrySettings,
    SecuritySettings,
)


def test_circuit_breaker_settings_defaults():
    settings = CircuitBreakerSettings()

    assert settings.failure_threshold == 3
    assert settings.recovery_timeout == 5
    assert settings.success_threshold == 2


def test_client_settings_defaults_to_empty_base_url():
    settings = ClientSettings()

    assert settings.base_url == ""


def test_limits_settings_defaults():
    settings = LimitsSettings()

    assert settings.timeout == 30
    assert settings.keep_alive_timeout == 60
    assert settings.ttl_dns_cache == 600
    assert settings.max_connections == 1000
    assert settings.max_connections_per_host == 100
    assert settings.max_keepalive_connections == 50


def test_security_settings_defaults_to_none():
    settings = SecuritySettings()

    assert settings.certificate is None
    assert settings.tls_cipher_spec is None


def test_retry_settings_defaults():
    settings = RetrySettings()

    assert settings.retry_count == 4
    assert settings.retry_delay == 5
    assert settings.retry_on == (Exception,)


def test_retry_settings_rejects_empty_retry_on():
    with pytest.raises(RuntimeError, match="retry_on cannot be empty"):
        RetrySettings(retry_on=())


def test_http_client_settings_builds_all_sub_settings_with_defaults():
    settings = HttpClientSettings()

    assert isinstance(settings.client_params, ClientSettings)
    assert isinstance(settings.limits, LimitsSettings)
    assert isinstance(settings.retry, RetrySettings)
    assert isinstance(settings.circuit_breaker, CircuitBreakerSettings)
    assert isinstance(settings.security, SecuritySettings)


def test_http_client_settings_sub_settings_are_independent_instances():
    first = HttpClientSettings()
    second = HttpClientSettings()

    assert first.limits is not second.limits
