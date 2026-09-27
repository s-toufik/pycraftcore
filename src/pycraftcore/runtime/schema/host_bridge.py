from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

type HostBridgeHandler = Callable[[str, dict[str, Any]], Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class HostBridgeConfig:
    host: str
    port: int
    token: str
    function_names: tuple[str, ...] = field(default=())
