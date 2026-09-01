from collections.abc import Awaitable, Callable
from typing import ParamSpec, Protocol, TypeVar

from pycraftcore.http.configuration.retry_configuration import RetrySettings

P = ParamSpec("P")
R = TypeVar("R")


class Retry(Protocol):
    @property
    def settings(self) -> RetrySettings: ...
    def decorator(self, func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]: ...
