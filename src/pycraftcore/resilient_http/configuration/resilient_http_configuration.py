from dataclasses import dataclass, field

from pycraftcore.circuit_breaker.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.http.configuration.http_client_configuration import HttpClientSettings
from pycraftcore.http.policy.http_error_policy import is_business_error, is_retryable
from pycraftcore.retry.configuration.retry_configuration import RetrySettings


def default_retry_settings() -> RetrySettings:
    return RetrySettings(should_retry=is_retryable)


def default_circuit_breaker_settings() -> CircuitBreakerSettings:
    return CircuitBreakerSettings(is_excluded=is_business_error, name="http")


@dataclass(slots=True)
class ResilientHttpSettings:
    
    http: HttpClientSettings = field(default_factory=HttpClientSettings)
    retry: RetrySettings = field(default_factory=default_retry_settings)
    circuit_breaker: CircuitBreakerSettings = field(
        default_factory=default_circuit_breaker_settings
    )