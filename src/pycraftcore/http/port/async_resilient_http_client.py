from collections.abc import Awaitable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AsyncResilientHttpClient(Protocol):
    def get(self, *args: Any, **kwargs: Any) -> Awaitable[Any]: ...
    def post(self, *args: Any, **kwargs: Any) -> Awaitable[Any]: ...
