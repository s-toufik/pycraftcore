from collections.abc import AsyncGenerator, Callable, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import BaseRoute, Mount

from pycraftcore.web.middleware import RequestIDMiddleware
from pycraftcore.web.schema import ApiSettings


def create_app(
    api: ApiSettings,
    *,
    routes: Sequence[BaseRoute],
    lifespan: Callable[[], AbstractAsyncContextManager[None]] | None = None,
    middleware: Sequence[Middleware] = (),
) -> Starlette:
    return Starlette(
        routes=[Mount(api.base_path, routes=list(routes))] if api.base_path else list(routes),
        middleware=[*_cors(api), Middleware(RequestIDMiddleware), *middleware],
        lifespan=None if lifespan is None else _lifespan(lifespan),
    )


def _lifespan(
    lifespan: Callable[[], AbstractAsyncContextManager[None]],
) -> Callable[[Starlette], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def run(_app: Starlette) -> AsyncGenerator[None]:
        async with lifespan():
            yield

    return run


def _cors(api: ApiSettings) -> list[Middleware]:
    if not api.cors_origins:
        return []
    return [
        Middleware(
            CORSMiddleware,
            allow_origins=list(api.cors_origins),
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
