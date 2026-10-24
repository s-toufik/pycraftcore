from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from litestar import Litestar, Request, Response, Router
from litestar import route as http_route
from litestar.config.cors import CORSConfig
from litestar.handlers import HTTPRouteHandler
from litestar.params import JSONBody
from litestar.response import Stream

from pycraftcore.web.schema.http_route import HttpResult, HttpRoute, ResponseKind
from pycraftcore.web.schema.web_application import WebApplication
from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE

JSON_MEDIA_TYPE: str = "application/json"


class LitestarApplicationFactory:
    def create(self, application: WebApplication) -> Litestar:
        @asynccontextmanager
        async def lifespan(app: Litestar) -> AsyncGenerator[None]:
            async with application.lifespan():
                app.register(
                    Router(
                        path=application.base_path,
                        route_handlers=[_handler(route) for route in application.routes()],
                    )
                )
                yield

        return Litestar(
            route_handlers=[],
            lifespan=[lifespan],
            middleware=list(application.middleware),
            cors_config=(
                CORSConfig(allow_origins=list(application.cors_origins))
                if application.cors_origins
                else None
            ),
            exception_handlers={
                error: _error_handler(status_code)
                for error, status_code in application.errors.items()
            },
            openapi_config=None,
            logging_config=None,
        )


def _handler(route: HttpRoute) -> HTTPRouteHandler:
    is_stream = route.kind is ResponseKind.EVENT_STREAM

    async def respond(*arguments: Any) -> Any:
        result = await route.handler(*arguments)
        if is_stream:
            return Stream(
                result, media_type=EVENT_STREAM_MEDIA_TYPE, headers=dict(EVENT_STREAM_HEADERS)
            )
        if isinstance(result, HttpResult):
            return Response(result.body, status_code=result.status_code)
        return result

    if route.body is None:

        async def handler() -> Any:
            return await respond()

    else:

        async def handler(data: Any) -> Any:
            return await respond(data)

        handler.__annotations__["data"] = JSONBody[route.body]  # ty: ignore[invalid-type-form]

    return http_route(
        route.path,
        http_method=[route.method],
        status_code=route.status_code,
        media_type=EVENT_STREAM_MEDIA_TYPE if is_stream else JSON_MEDIA_TYPE,
        tags=list(route.tags) or None,
    )(handler)


def _error_handler(status_code: int) -> Callable[[Request, Exception], Response]:
    def handle(_request: Request, exception: Exception) -> Response:
        return Response({"detail": str(exception)}, status_code=status_code)

    return handle
