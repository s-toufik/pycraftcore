from collections.abc import Callable
from dataclasses import dataclass


@dataclass(slots=True)
class CircuitBreakerSettings:
    failure_threshold: int = 3
    recovery_timeout: float = 5.0
    excluded_exceptions: tuple[type[Exception], ...] = ()
    is_excluded: Callable[[BaseException], bool] | None = None
    name: str = "default"

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be greater than or equal to 1")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be greater than 0")
