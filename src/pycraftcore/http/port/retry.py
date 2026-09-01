from collections.abc import Awaitable, Callable
from typing import ParamSpec, Protocol, TypeVar, runtime_checkable

from pycraftcore.http.configuration.retry_configuration import RetrySettings

P = ParamSpec("P")
R = TypeVar("R")


@runtime_checkable
class Retry(Protocol):
    @property
    def settings(self) -> RetrySettings: ...
    def decorator(self, func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]: ...
