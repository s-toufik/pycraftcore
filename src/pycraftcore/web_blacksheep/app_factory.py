from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any

from blacksheep import Application, Request, Response, Router
from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import Info

from pycraftcore.web.asgi import ASGIApp
from pycraftcore.web.middleware import RequestIDMiddleware
from pycraftcore.web.schema import DOCS_PATH, OPENAPI_PATH, ApiSettings

type ExceptionHandler = Callable[[Application, Request, Exception], Awaitable[Response]]
type Middleware = Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]


def create_app(
    api: ApiSettings,
    *,
    routes: Sequence[Router],
    lifespan: Callable[[], AbstractAsyncContextManager[None]] | None = None,
    middleware: Sequence[Middleware] = (),
    exception_handlers: Mapping[int | type[Exception], ExceptionHandler] | None = None,
    openapi: OpenAPIHandler | None = None,
    **options: Any,
) -> ASGIApp:
    app = Application(router=_mount(routes, Router(prefix=api.base_path)), **options)
    if lifespan is not None:
        app.lifespan(_lifespan(lifespan))
    docs = (openapi or openapi_handler(api)) if api.docs else None
    if docs is not None:
        docs.bind_app(app)
    if api.cors_origins:
        app.use_cors(allow_origins=list(api.cors_origins), allow_methods="*", allow_headers="*")
    for error, handler in (exception_handlers or {}).items():
        app.exception_handler(error)(handler)
    for handler in middleware:
        app.middlewares.append(handler)
    return RequestIDMiddleware(app)


def _mount(routes: Sequence[Router], router: Router) -> Router:
    for source in routes:
        source.apply_routes()
        for method, route in source.iter_with_methods():
            router.add(method, route.pattern, route.handler)
    return router


def openapi_handler(api: ApiSettings) -> OpenAPIHandler:
    return OpenAPIHandler(
        info=Info(title=api.title, version=api.version),
        ui_path=DOCS_PATH,
        json_spec_path=OPENAPI_PATH,
        yaml_spec_path=f"{DOCS_PATH}/openapi.yaml",
    )


def _lifespan(
    lifespan: Callable[[], AbstractAsyncContextManager[None]],
) -> Callable[[], AsyncGenerator[None]]:
    async def run() -> AsyncGenerator[None]:
        async with lifespan():
            yield

    return run
