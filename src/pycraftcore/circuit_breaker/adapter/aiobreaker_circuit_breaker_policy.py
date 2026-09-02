from asyncio import Lock
from collections.abc import Callable, Coroutine, Iterable
from datetime import timedelta
from typing import Any, ParamSpec, TypeVar

from aiobreaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerListener,
    CircuitBreakerState,
)

from pycraftcore.circuit_breaker.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from pycraftcore.circuit_breaker.enum.circuit_breaker_status import CircuitState
from pycraftcore.circuit_breaker.exception.circuit_breaker_open_exception import (
    CircuitBreakerOpenException,
)
from pycraftcore.logger.port.logger import Logger

P = ParamSpec("P")
R = TypeVar("R")

STATE_MAPPING: dict[CircuitBreakerState, CircuitState] = {
    CircuitBreakerState.CLOSED: CircuitState.CLOSED,
    CircuitBreakerState.OPEN: CircuitState.OPEN,
    CircuitBreakerState.HALF_OPEN: CircuitState.HALF_OPEN,
}


class CircuitBreakerLogger(CircuitBreakerListener):
    """Bridges aiobreaker state changes onto the `Logger` port."""

    def __init__(self, settings: CircuitBreakerSettings, logger: Logger | None = None) -> None:
        self._settings: CircuitBreakerSettings = settings
        self._logger: Logger | None = logger

    def failure(self, breaker: CircuitBreaker, exception: Exception) -> None:
        if self._logger:
            self._logger.warning(
                f"Circuit breaker '{self._settings.name}' recorded failure "
                f"{breaker.fail_counter}/{breaker.fail_max}: {exception!r}"
            )

    def success(self, breaker: CircuitBreaker) -> None:
        return None

    def state_change(self, breaker: CircuitBreaker, old: object, new: object) -> None:
        """aiobreaker hands over state *objects*, not enum members."""

        if not self._logger:
            return

        self._logger.info(
            f"Circuit breaker '{self._settings.name}' moved from "
            f"{self._state_name(old)} to {self._state_name(new)}"
        )

        if getattr(new, "state", None) is CircuitBreakerState.OPEN:
            self._logger.error(
                f"Circuit breaker '{self._settings.name}' is OPEN after "
                f"{breaker.fail_max} failures; calls are rejected for "
                f"{self._settings.recovery_timeout:.1f} seconds"
            )

    @staticmethod
    def _state_name(state: object) -> str:
        return getattr(getattr(state, "state", state), "name", "UNKNOWN")


class AioBreakerCircuitBreakerPolicy:
    def __init__(
        self,
        settings: CircuitBreakerSettings | None = None,
        logger: Logger | None = None,
    ) -> None:
        self._settings: CircuitBreakerSettings = settings or CircuitBreakerSettings()
        self._logger: Logger | None = logger
        self._probe_lock: Lock = Lock()
        self._breaker: CircuitBreaker = CircuitBreaker(
            fail_max=self._settings.failure_threshold,
            timeout_duration=timedelta(seconds=self._settings.recovery_timeout),
            exclude=self._exclusions(),
            listeners=[CircuitBreakerLogger(self._settings, logger)],
            name=self._settings.name,
        )

    @property
    def settings(self) -> CircuitBreakerSettings:
        return self._settings

    @property
    def state(self) -> CircuitState:
        return STATE_MAPPING[self._breaker.current_state]

    @property
    def failure_count(self) -> int:
        return self._breaker.fail_counter

    async def call(
        self,
        func: Callable[P, Coroutine[Any, Any, R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        if self._breaker.current_state is CircuitBreakerState.CLOSED:
            return await self._call(func, *args, **kwargs)

        async with self._probe_lock:
            return await self._call(func, *args, **kwargs)

    async def _call(
        self,
        func: Callable[P, Coroutine[Any, Any, R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        try:
            return await self._breaker.call_async(func, *args, **kwargs)

        except CircuitBreakerError as error:
            raise self._translate(error) from None

    def _translate(self, error: CircuitBreakerError) -> BaseException:

        if error.__cause__ is not None:
            return error.__cause__

        return CircuitBreakerOpenException(
            f"Circuit breaker '{self._settings.name}' is open; "
            f"calls are rejected for up to {self._settings.recovery_timeout:.1f} seconds"
        )

    def _exclusions(self) -> Iterable[type[Exception] | Callable[[BaseException], bool]]:
        exclusions: list[type[Exception] | Callable[[BaseException], bool]] = [
            *self._settings.excluded_exceptions
        ]

        if self._settings.is_excluded is not None:
            exclusions.append(self._settings.is_excluded)

        return exclusions
