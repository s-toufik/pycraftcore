from collections.abc import AsyncGenerator, Awaitable, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from pycraftcore.web.schema.http_route import HttpResult, HttpRoute, ResponseKind
from pycraftcore.web.schema.web_application import WebApplication
from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE

type _ErrorHandler = Callable[[Request, Any], Coroutine[Any, Any, Response]]


class _EventStreamResponse(StreamingResponse):
    media_type = EVENT_STREAM_MEDIA_TYPE


class FastApiApplicationFactory:
    def create(self, application: WebApplication) -> FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
            async with application.lifespan():
                app.include_router(_router(application))
                yield

        return FastAPI(
            title=application.title,
            version=application.version,
            lifespan=lifespan,
            middleware=[
                *_cors(application),
                *(Middleware(middleware) for middleware in application.middleware),
            ],
            exception_handlers=_error_handlers(application),
            docs_url=application.docs_path if application.docs else None,
            redoc_url=None,
            openapi_url=application.openapi_path if application.docs else None,
        )


def _router(application: WebApplication) -> APIRouter:
    router = APIRouter(prefix=application.base_path)
    for route in application.routes():
        router.add_api_route(
            route.path,
            _endpoint(route),
            methods=[route.method],
            status_code=route.status_code,
            response_class=(
                _EventStreamResponse if route.kind is ResponseKind.EVENT_STREAM else JSONResponse
            ),
            tags=list(route.tags) or None,
        )
    return router


def _endpoint(route: HttpRoute) -> Callable[..., Awaitable[Any]]:
    if route.body is None:

        async def endpoint() -> Any:
            return _respond(route, await route.handler())

    else:

        async def endpoint(data: Any) -> Any:
            return _respond(route, await route.handler(data))

        endpoint.__annotations__["data"] = route.body

    endpoint.__annotations__["return"] = route.response or Any
    return endpoint


def _respond(route: HttpRoute, result: Any) -> Any:
    if route.kind is ResponseKind.EVENT_STREAM:
        return _EventStreamResponse(result, headers=dict(EVENT_STREAM_HEADERS))
    if isinstance(result, HttpResult):
        return JSONResponse(result.body.model_dump(mode="json"), result.status_code)
    return result


def _cors(application: WebApplication) -> list[Middleware]:
    if not application.cors_origins:
        return []
    return [
        Middleware(
            CORSMiddleware,
            allow_origins=list(application.cors_origins),
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]


def _error_handlers(application: WebApplication) -> dict[int | type[Exception], _ErrorHandler]:
    return {error: _error_handler(status_code) for error, status_code in application.errors.items()}


def _error_handler(status_code: int) -> _ErrorHandler:
    async def handle(_request: Request, exception: Exception) -> Response:
        return JSONResponse({"detail": str(exception)}, status_code=status_code)

    return handle
