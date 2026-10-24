from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from litestar import Litestar, MediaType, Request, Response, Router
from litestar import route as http_route
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.params import JSONBody
from litestar.response import Stream
from litestar.types import ExceptionHandlersMap

from pycraftcore.web.schema.http_route import HttpResult, HttpRoute, ResponseKind
from pycraftcore.web.schema.web_application import WebApplication
from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE

type _ErrorHandler = Callable[[Request, Exception], Response]


class LitestarApplicationFactory:
    def create(self, application: WebApplication) -> Litestar:
        @asynccontextmanager
        async def lifespan(app: Litestar) -> AsyncGenerator[None]:
            async with application.lifespan():
                app.register(_router(application))
                yield

        return Litestar(
            lifespan=[lifespan],
            middleware=list(application.middleware),
            cors_config=_cors(application),
            exception_handlers=_error_handlers(application),
            openapi_config=(
                OpenAPIConfig(
                    title=application.title,
                    version=application.version,
                    path=application.docs_path,
                    render_plugins=[SwaggerRenderPlugin(path="/")],
                )
                if application.docs
                else None
            ),
            logging_config=None,
        )


def _router(application: WebApplication) -> Router:
    router = Router(path=application.base_path, route_handlers=[])
    for route in application.routes():
        router.register(
            http_route(
                route.path,
                http_method=[route.method],
                status_code=route.status_code,
                media_type=(
                    EVENT_STREAM_MEDIA_TYPE
                    if route.kind is ResponseKind.EVENT_STREAM
                    else MediaType.JSON
                ),
                tags=list(route.tags) or None,
            )(_endpoint(route))
        )
    return router


def _endpoint(route: HttpRoute) -> Callable[..., Awaitable[Any]]:
    if route.body is None:

        async def endpoint() -> Any:
            return _respond(route, await route.handler())

    else:

        async def endpoint(data: Any) -> Any:
            return _respond(route, await route.handler(data))

        endpoint.__annotations__["data"] = JSONBody[route.body]  # ty: ignore[invalid-type-form]

    endpoint.__annotations__["return"] = route.response or Any
    return endpoint


def _respond(route: HttpRoute, result: Any) -> Any:
    if route.kind is ResponseKind.EVENT_STREAM:
        return Stream(
            result, media_type=EVENT_STREAM_MEDIA_TYPE, headers=dict(EVENT_STREAM_HEADERS)
        )
    if isinstance(result, HttpResult):
        return Response(result.body, status_code=result.status_code)
    return result


def _cors(application: WebApplication) -> CORSConfig | None:
    if not application.cors_origins:
        return None
    return CORSConfig(allow_origins=list(application.cors_origins))


def _error_handlers(application: WebApplication) -> ExceptionHandlersMap:
    return {error: _error_handler(status_code) for error, status_code in application.errors.items()}


def _error_handler(status_code: int) -> _ErrorHandler:
    def handle(_request: Request, exception: Exception) -> Response:
        return Response({"detail": str(exception)}, status_code=status_code)

    return handle
