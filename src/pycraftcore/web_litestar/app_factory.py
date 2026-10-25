from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any

from litestar import Litestar, Router
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.types import ControllerRouterHandler, ExceptionHandlersMap, Middleware

from pycraftcore.web.asgi import AsgiMiddleware
from pycraftcore.web.middleware import RequestIDMiddleware
from pycraftcore.web.schema import ApiSettings

REQUEST_ID: AsgiMiddleware = RequestIDMiddleware


def create_app(
    api: ApiSettings,
    *,
    routes: Sequence[ControllerRouterHandler],
    lifespan: Callable[[], AbstractAsyncContextManager[None]] | None = None,
    middleware: Sequence[Middleware] = (),
    exception_handlers: ExceptionHandlersMap | None = None,
    **options: Any,
) -> Litestar:
    return Litestar(
        route_handlers=[Router(path=api.base_path, route_handlers=list(routes))],
        lifespan=[] if lifespan is None else [lambda _app: lifespan()],
        middleware=[REQUEST_ID, *middleware],
        exception_handlers=exception_handlers or {},
        **(_conventions(api) | options),
    )


def _conventions(api: ApiSettings) -> dict[str, Any]:
    return {"cors_config": _cors(api), "openapi_config": _docs(api), "logging_config": None}


def _cors(api: ApiSettings) -> CORSConfig | None:
    if not api.cors_origins:
        return None
    return CORSConfig(allow_origins=list(api.cors_origins))


def _docs(api: ApiSettings) -> OpenAPIConfig | None:
    if not api.docs:
        return None
    return OpenAPIConfig(
        title=api.title,
        version=api.version,
        path=api.docs_path,
        render_plugins=[SwaggerRenderPlugin(path="/")],
    )
