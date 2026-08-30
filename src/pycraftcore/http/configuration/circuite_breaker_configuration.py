from dataclasses import dataclass


@dataclass(slots=True)
class CircuitBreakerSettings:
    failure_threshold: int = 3
    recovery_timeout: float = 5
    success_threshold: int = 2
