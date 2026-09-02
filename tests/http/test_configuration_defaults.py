from pycraftcore.http.configuration import (
    ClientSettings,
    HttpClientSettings,
    LimitsSettings,
    SecuritySettings,
)


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


def test_http_client_settings_builds_all_sub_settings_with_defaults():
    settings = HttpClientSettings()

    assert isinstance(settings.client_params, ClientSettings)
    assert isinstance(settings.limits, LimitsSettings)
    assert isinstance(settings.security, SecuritySettings)


def test_http_client_settings_sub_settings_are_independent_instances():
    first = HttpClientSettings()
    second = HttpClientSettings()

    assert first.limits is not second.limits
    assert first.client_params is not second.client_params
    assert first.security is not second.security


def test_http_client_settings_has_no_resilience_fields():
    # Retry/circuit-breaker policy belongs to ResilientHttpSettings, not the
    # plain transport settings, so HttpClientSettings must not carry them.
    settings = HttpClientSettings()

    assert not hasattr(settings, "retry")
    assert not hasattr(settings, "circuit_breaker")
