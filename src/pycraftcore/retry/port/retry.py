from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, Protocol, TypeVar, runtime_checkable

from pycraftcore.retry.configuration.retry_configuration import RetrySettings

P = ParamSpec("P")
R = TypeVar("R")


@runtime_checkable
class Retry(Protocol):
    @property
    def settings(self) -> RetrySettings: ...
    def decorator(
        self, func: Callable[P, Coroutine[Any, Any, R]]
    ) -> Callable[P, Coroutine[Any, Any, R]]: ...
