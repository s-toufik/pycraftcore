import time
from asyncio import Lock
from typing import ParamSpec

from pycraftcore.http.configuration.circuite_breaker_configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.http.enum.circuit_breaker_status import CircuitState
from pycraftcore.http.exception.circuit_breaker_open_exception import (
    CircuitBreakerOpenException,
)

P = ParamSpec("P")


class CircuitBreakerPolicy:
    def __init__(self, settings: CircuitBreakerSettings | None = None):

        self._settings = settings or CircuitBreakerSettings()
        self._state: CircuitState = CircuitState.CLOSED
        self._failure_counter: int = 0
        self._success_counter: int = 0
        self._last_failure_time: float = 0
        self._last_exception: Exception | None = None

        self._clock = time.time
        self._lock = Lock()

    @property
    def settings(self) -> CircuitBreakerSettings:
        return self._settings

    @property
    def last_exception(self) -> Exception | None:
        return self._last_exception

    @property
    def state(self) -> CircuitState:
        return self._state

    def _can_attempt(self) -> bool:

        # CLOSED
        if self._state == CircuitState.CLOSED:
            return True

        # OPEN
        if self._state == CircuitState.OPEN:
            return self._clock() - self._last_failure_time >= self._settings.recovery_timeout

        # HALF OPEN
        return True

    def _on_success(self) -> None:

        if self._state == CircuitState.HALF_OPEN:
            self._success_counter += 1
            if self._success_counter >= self._settings.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_counter = 0
                self._success_counter = 0
                self._last_exception = None

        else:
            self._failure_counter = 0

    def _on_failure(self, exception: Exception) -> None:

        self._failure_counter += 1
        self._last_failure_time = self._clock()
        self._last_exception = exception

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._success_counter = 0
            return

        if self._failure_counter >= self._settings.failure_threshold:
            self._state = CircuitState.OPEN

    async def call(self, func, *args: P.args, **kwargs: P.kwargs):
        async with self._lock:
            if not self._can_attempt():
                raise CircuitBreakerOpenException(
                    f"Circuit breaker open (last failure: {self._last_exception})"
                )
            if self._state == CircuitState.OPEN:
                self._state = CircuitState.HALF_OPEN
                self._success_counter = 0

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self._on_success()
            return result

        except Exception as exception:
            async with self._lock:
                self._on_failure(exception)
            raise