import pytest

from pycraftcore.circuit_breaker.exception.circuit_breaker_open_exception import (
    CircuitBreakerOpenException,
)


def test_is_an_exception():
    with pytest.raises(CircuitBreakerOpenException, match="circuit open"):
        raise CircuitBreakerOpenException("circuit open")
