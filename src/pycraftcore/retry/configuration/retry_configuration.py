from collections.abc import Callable
from dataclasses import dataclass


@dataclass(slots=True)
class RetrySettings:
    retry_count: int = 4
    retry_delay: float = 5
    retry_on: tuple[type[Exception], ...] = (Exception,)
    max_retry_delay: float = 8.0
    jitter: float = 0.5
    should_retry: Callable[[BaseException], bool] | None = None

    def __post_init__(self) -> None:
        if self.retry_count < 0:
            raise ValueError("retry_count must be greater than or equal to 0")
        if self.retry_delay <= 0:
            raise ValueError("retry_delay must be greater than 0")
        if self.max_retry_delay < self.retry_delay:
            raise ValueError("max_retry_delay must be greater than or equal to retry_delay")
        if self.jitter < 0:
            raise ValueError("jitter must be greater than or equal to 0")
        if self.should_retry is None and not self.retry_on:
            raise ValueError("retry_on cannot be empty when should_retry is not provided")

    @property
    def attempts(self) -> int:
        return self.retry_count + 1
