from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from pycraftcore.web.schema.http_route import HttpResult, HttpRoute, ResponseKind
from pycraftcore.web.schema.web_application import WebApplication
from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE


class FastApiApplicationFactory:
    def create(self, application: WebApplication) -> FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
            async with application.lifespan():
                router = APIRouter()
                for route in application.routes():
                    router.add_api_route(
                        route.path,
                        _endpoint(route),
                        methods=[route.method],
                        status_code=route.status_code,
                        response_model=route.response,
                        tags=list(route.tags) or None,
                    )
                app.include_router(router)
                yield

        app = FastAPI(title=application.title, lifespan=lifespan)

        for error, status_code in application.errors.items():
            app.add_exception_handler(error, _error_handler(status_code))

        for middleware in reversed(application.middleware):
            app.add_middleware(middleware)
        if application.cors_origins:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=list(application.cors_origins),
                allow_methods=["*"],
                allow_headers=["*"],
            )
        return app


def _endpoint(route: HttpRoute) -> Callable[..., Awaitable[Any]]:
    async def respond(*arguments: Any) -> Any:
        result = await route.handler(*arguments)
        if route.kind is ResponseKind.EVENT_STREAM:
            return StreamingResponse(
                result, media_type=EVENT_STREAM_MEDIA_TYPE, headers=dict(EVENT_STREAM_HEADERS)
            )
        if isinstance(result, HttpResult):
            return JSONResponse(result.body.model_dump(mode="json"), result.status_code)
        return result

    if route.body is None:

        async def endpoint() -> Any:
            return await respond()

        return endpoint

    async def endpoint_with_body(data: Any) -> Any:
        return await respond(data)

    endpoint_with_body.__annotations__["data"] = route.body
    return endpoint_with_body


def _error_handler(status_code: int) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def handle(_request: Request, exception: Exception) -> JSONResponse:
        return JSONResponse({"detail": str(exception)}, status_code=status_code)

    return handle
