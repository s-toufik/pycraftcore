import json as jsonlib
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from contextlib import aclosing
from typing import Any

from blacksheep import Application, Request, Response, StreamedContent, json
from blacksheep.server.routing import Router
from pydantic import BaseModel, ValidationError

from pycraftcore.web.asgi import ASGIApp
from pycraftcore.web.schema.http_route import HttpResult, HttpRoute, ResponseKind
from pycraftcore.web.schema.web_application import WebApplication
from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE
from pycraftcore.web.streaming import Idle, with_idle_ticks

DISCONNECT_CHECK_SECONDS: float = 1.0


class BlackSheepApplicationFactory:
    def create(self, application: WebApplication) -> ASGIApp:
        app = Application(router=Router())
        app.lifespan(_with_routes(app, application))

        for error, status_code in application.errors.items():
            app.exceptions_handlers[error] = _error_handler(status_code)

        if application.cors_origins:
            app.use_cors(
                allow_origins=list(application.cors_origins),
                allow_methods="*",
                allow_headers="*",
            )

        asgi: ASGIApp = app
        for middleware in reversed(application.middleware):
            asgi = middleware(asgi)
        return asgi


def _with_routes(
    app: Application, application: WebApplication
) -> Callable[[Application], AsyncGenerator[None]]:
    async def lifespan(_app: Application) -> AsyncGenerator[None]:
        async with application.lifespan():
            for route in application.routes():
                app.router.add(route.method, route.path, _handler(route))
            app.router.apply_routes()
            yield

    return lifespan


def _handler(route: HttpRoute) -> Callable[[Request], Awaitable[Response]]:
    async def handler(request: Request) -> Response:
        arguments: list[BaseModel] = []
        if route.body is not None:
            try:
                arguments.append(route.body.model_validate(await request.json()))
            except (ValidationError, jsonlib.JSONDecodeError, ValueError) as error:
                return json({"detail": _describe(error)}, status=400)

        result = await route.handler(*arguments)

        if route.kind is ResponseKind.EVENT_STREAM:
            return Response(
                route.status_code,
                [(name.encode(), value.encode()) for name, value in EVENT_STREAM_HEADERS.items()],
                StreamedContent(EVENT_STREAM_MEDIA_TYPE.encode(), _frames(result, request)),
            )
        if isinstance(result, HttpResult):
            return json(result.body.model_dump(mode="json"), status=result.status_code)
        body = result.model_dump(mode="json") if isinstance(result, BaseModel) else result
        return json(body, status=route.status_code)

    return handler


def _frames(frames: AsyncIterator[bytes], request: Request) -> Callable[[], AsyncGenerator[bytes]]:
    async def until_disconnected() -> AsyncGenerator[bytes]:
        async with aclosing(with_idle_ticks(frames, DISCONNECT_CHECK_SECONDS)) as ticks:
            async for frame in ticks:
                if await request.is_disconnected():
                    return
                if not isinstance(frame, Idle):
                    yield frame

    return until_disconnected


def _describe(error: Exception) -> Any:
    if isinstance(error, ValidationError):
        return error.errors(include_url=False, include_context=False, include_input=False)
    return str(error)


def _error_handler(
    status_code: int,
) -> Callable[[Application, Request, Exception], Awaitable[Response]]:
    async def handle(_app: Application, _request: Request, exception: Exception) -> Response:
        return json({"detail": str(exception)}, status=status_code)

    return handle
