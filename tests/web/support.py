import asyncio
import socket
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import httpx
import pytest
import uvicorn
from asgi_lifespan import LifespanManager

from pycraftcore.web.asgi import ASGIApp, AsgiMiddleware
from pycraftcore.web.enum.web_framework import WebFramework
from pycraftcore.web.frameworks import web_application_factory
from pycraftcore.web.schema.http_route import HttpRoute
from pycraftcore.web.schema.web_application import WebApplication

EVERY_FRAMEWORK = pytest.mark.parametrize("framework", list(WebFramework), ids=str)


@asynccontextmanager
async def nothing() -> AsyncIterator[None]:
    yield


def build_app(
    framework: WebFramework,
    routes: Sequence[HttpRoute],
    *,
    lifespan: Callable[[], AbstractAsyncContextManager[None]] = nothing,
    errors: Mapping[type[Exception], int] | None = None,
    middleware: Sequence[AsgiMiddleware] = (),
    cors_origins: Sequence[str] = (),
) -> ASGIApp:
    application = WebApplication(
        title="orders-api",
        lifespan=lifespan,
        routes=lambda: routes,
        errors=errors or {},
        middleware=middleware,
        cors_origins=cors_origins,
    )
    return web_application_factory(framework).create(application)


@asynccontextmanager
async def http_client(app: ASGIApp) -> AsyncGenerator[httpx.AsyncClient]:
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@asynccontextmanager
async def running_server(app: ASGIApp) -> AsyncGenerator[str]:
    port = free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    task = asyncio.create_task(server.serve())
    try:
        while not server.started:
            if task.done():
                raise RuntimeError("the server did not start")
            await asyncio.sleep(0.01)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await task


async def starts(app: ASGIApp) -> bool:
    config = uvicorn.Config(app, port=free_port(), log_config=None, log_level="error")
    server = uvicorn.Server(config)

    async def stop_once_started() -> None:
        while not server.started:
            await asyncio.sleep(0.01)
        server.should_exit = True

    watcher = asyncio.create_task(stop_once_started())
    try:
        await asyncio.wait_for(server.serve(), timeout=10)
    except SystemExit:
        pass
    finally:
        watcher.cancel()
    return server.started
