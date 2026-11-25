from collections.abc import AsyncGenerator, Callable, Iterable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.routing import BaseRoute

from pycraftcore.application_configuration.model import McpConnector
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web_starlette.app_factory import create_app as create_starlette_app

DEFAULT_MCP_PATH: str = "/mcp"


def mcp_path(connector: McpConnector) -> str:
    return urlparse(connector.base_url).path.rstrip("/") or DEFAULT_MCP_PATH


def create_app(
    api: ApiSettings,
    servers: Mapping[str, MCPServer],
    connector: McpConnector,
    *,
    routes: Sequence[BaseRoute] = (),
    middleware: Sequence[Middleware] = (),
    lifespan: Callable[[], AbstractAsyncContextManager[None]] | None = None,
    allowed_hosts: Iterable[str] = (),
) -> Starlette:
    host: str = urlparse(connector.base_url).netloc
    security = TransportSecuritySettings(allowed_hosts=[*([host] if host else []), *allowed_hosts])
    children: list[Starlette] = [
        server.streamable_http_app(
            streamable_http_path=path,
            json_response=True,
            stateless_http=True,
            transport_security=security,
        )
        for path, server in servers.items()
    ]
    return create_starlette_app(
        api,
        routes=[*routes, *(route for child in children for route in child.routes)],
        middleware=[Middleware(GZipMiddleware, minimum_size=1024), *middleware],
        lifespan=_running(children, lifespan),
    )


def _running(
    children: list[Starlette],
    lifespan: Callable[[], AbstractAsyncContextManager[None]] | None,
) -> Callable[[], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def run() -> AsyncGenerator[None]:
        async with AsyncExitStack() as stack:
            for child in children:
                await stack.enter_async_context(child.router.lifespan_context(child))
            if lifespan is not None:
                await stack.enter_async_context(lifespan())
            yield

    return run
