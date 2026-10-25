from collections.abc import Callable, Coroutine, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from pycraftcore.web.middleware import RequestIDMiddleware
from pycraftcore.web.schema import ApiSettings

type ExceptionHandler = Callable[[Request, Any], Coroutine[Any, Any, Response]]


def create_app(
    api: ApiSettings,
    *,
    routes: Sequence[APIRouter],
    lifespan: Callable[[], AbstractAsyncContextManager[None]] | None = None,
    middleware: Sequence[Middleware] = (),
    exception_handlers: Mapping[int | type[Exception], ExceptionHandler] | None = None,
    **options: Any,
) -> FastAPI:
    app = FastAPI(
        lifespan=None if lifespan is None else _lifespan(lifespan),
        middleware=[*_cors(api), Middleware(RequestIDMiddleware), *middleware],
        exception_handlers=dict(exception_handlers or {}),
        **(_conventions(api) | options),
    )
    for router in routes:
        app.include_router(router, prefix=api.base_path)
    return app


def _conventions(api: ApiSettings) -> dict[str, Any]:
    return {
        "title": api.title,
        "version": api.version,
        "docs_url": api.docs_path if api.docs else None,
        "redoc_url": None,
        "openapi_url": api.openapi_path if api.docs else None,
    }


def _lifespan(
    lifespan: Callable[[], AbstractAsyncContextManager[None]],
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    def run(_app: FastAPI) -> AbstractAsyncContextManager[None]:
        return lifespan()

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
