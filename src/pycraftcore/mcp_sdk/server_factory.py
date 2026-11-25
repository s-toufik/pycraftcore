from typing import Any

from mcp.server._otel import OpenTelemetryMiddleware
from mcp.server.context import CallNext, HandlerResult, ServerMiddleware, ServerRequestContext
from mcp.server.mcpserver import MCPServer

_NOTIFICATION_PREFIX: str = "notifications/"


def create_server(name: str, version: str, instructions: str | None = None) -> MCPServer:
    server = MCPServer(name=name, version=version, instructions=instructions)
    server.middleware[:] = [
        _RequestSpans(middleware) if isinstance(middleware, OpenTelemetryMiddleware) else middleware
        for middleware in server.middleware
    ]
    return server


class _RequestSpans:
    def __init__(self, spans: ServerMiddleware[Any]) -> None:
        self._spans = spans

    async def __call__(
        self, ctx: ServerRequestContext[Any, Any], call_next: CallNext
    ) -> HandlerResult:
        if ctx.method.startswith(_NOTIFICATION_PREFIX):
            return await call_next(ctx)
        return await self._spans(ctx, call_next)
