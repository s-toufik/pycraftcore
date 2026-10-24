from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field

from pycraftcore.web.asgi import AsgiMiddleware
from pycraftcore.web.schema.http_route import HttpRoute


@dataclass(frozen=True, slots=True)
class WebApplication:
    title: str
    lifespan: Callable[[], AbstractAsyncContextManager[None]]
    routes: Callable[[], Sequence[HttpRoute]]
    base_path: str = ""
    errors: Mapping[type[Exception], int] = field(default_factory=dict)
    middleware: Sequence[AsgiMiddleware] = ()
    cors_origins: Sequence[str] = ()

    def __post_init__(self) -> None:
        if self.base_path and (not self.base_path.startswith("/") or self.base_path.endswith("/")):
            raise ValueError(
                f"base_path must start with '/' and must not end with '/': {self.base_path!r}"
            )
