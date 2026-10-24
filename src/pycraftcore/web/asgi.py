from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

type Scope = MutableMapping[str, Any]
type Message = MutableMapping[str, Any]
type Receive = Callable[[], Awaitable[Message]]
type Send = Callable[[Message], Awaitable[None]]
type ASGIApp = Callable[..., Awaitable[None]]
type AsgiMiddleware = Callable[[ASGIApp], ASGIApp]
