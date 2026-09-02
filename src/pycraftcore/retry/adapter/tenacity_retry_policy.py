from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from pycraftcore.retry.configuration.retry_configuration import RetrySettings
from pycraftcore.logger.port.logger import Logger

P = ParamSpec("P")
R = TypeVar("R")


class TenacityRetryPolicy:
    def __init__(self, settings: RetrySettings | None = None, logger: Logger | None = None) -> None:
        self._settings: RetrySettings = settings or RetrySettings()
        self._logger: Logger | None = logger

    @property
    def settings(self) -> RetrySettings:
        return self._settings

    def decorator(
        self, func: Callable[P, Coroutine[Any, Any, R]]
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        return self._retrying().wraps(func)

    def _retrying(self) -> AsyncRetrying:
        return AsyncRetrying(
            retry=retry_if_exception(self._should_retry),
            stop=stop_after_attempt(self._settings.attempts),
            wait=wait_exponential_jitter(
                initial=self._settings.retry_delay,
                max=self._settings.max_retry_delay,
                jitter=self._settings.jitter,
            ),
            reraise=True,
            before_sleep=self._log_retry,
        )

    def _should_retry(self, exception: BaseException) -> bool:
        if self._settings.should_retry is not None:
            return self._settings.should_retry(exception)

        return isinstance(exception, self._settings.retry_on)

    def _log_retry(self, retry_state: RetryCallState) -> None:
        if self._logger is None or retry_state.next_action is None:
            return

        exception = retry_state.outcome.exception() if retry_state.outcome else None
        self._logger.warning(
            f"Attempt {retry_state.attempt_number}/{self._settings.attempts} failed "
            f"with {exception!r}; retrying in {retry_state.next_action.sleep:.2f} seconds"
        )
