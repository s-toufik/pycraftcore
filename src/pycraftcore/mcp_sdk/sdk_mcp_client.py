import asyncio
import base64
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

import httpx2
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent

from pycraftcore.application_configuration.model import McpConnector, McpOperation
from pycraftcore.authentication import BasicAuth, TokenAuth
from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.logger.port import Logger
from pycraftcore.mcp.exception.mcp_unavailable_exception import McpUnavailableException
from pycraftcore.mcp.schema.call_result import CallResult
from pycraftcore.mcp.schema.remote_tool import RemoteTool


class SdkMcpClient:
    def __init__(
        self,
        connector: McpConnector,
        operation: McpOperation | None = None,
        logger: Logger | None = None,
        max_attempts: int = 3,
        initial_delay: float = 0.5,
        max_delay: float = 5.0,
    ) -> None:
        self._connector = connector
        self._operation = operation
        self._logger = logger
        self._max_attempts = max_attempts
        self._initial_delay = initial_delay
        self._max_delay = max_delay

    async def list_tools(self) -> list[RemoteTool]:
        async with self._session() as session:
            listed = await session.list_tools()
        return [
            RemoteTool(tool.name, tool.description or "", tool.input_schema, tool.output_schema)
            for tool in listed.tools
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallResult:
        async with self._session() as session:
            result = await session.call_tool(name, arguments)
        return CallResult(
            content=tuple(
                block.text if isinstance(block, TextContent) else str(block)
                for block in result.content
            ),
            structured=result.structured_content,
            is_error=bool(result.is_error),
        )

    @asynccontextmanager
    async def _session(self) -> AsyncGenerator[ClientSession]:
        try:
            async with AsyncExitStack() as stack:
                yield await self._connect_with_retry(stack)
        except McpUnavailableException:
            raise
        except Exception as error:
            raise McpUnavailableException(
                f"MCP server at {self._connector.base_url} failed: {root_causes(error)}"
            ) from error

    async def _connect_with_retry(self, stack: AsyncExitStack) -> ClientSession:
        delay: float = self._initial_delay
        last: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            attempt_stack = AsyncExitStack()
            try:
                session: ClientSession = await self._connect(attempt_stack)
                await stack.enter_async_context(attempt_stack)
                return session
            except BaseException as raised:
                last = await _close_failed_attempt(attempt_stack, raised)
                if self._logger is not None:
                    self._logger.warning(
                        f"MCP connection to {self._connector.base_url} failed "
                        f"(attempt {attempt}/{self._max_attempts}): {root_causes(last)}"
                    )
                if attempt < self._max_attempts:
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self._max_delay)
        raise McpUnavailableException(
            f"could not reach the MCP server at {self._connector.base_url} after "
            f"{self._max_attempts} attempts: {root_causes(last) if last else 'no attempt made'}"
        ) from last

    async def _connect(self, stack: AsyncExitStack) -> ClientSession:
        read, write = await self._open_transport(stack)
        session: ClientSession = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        return session

    async def _open_transport(self, stack: AsyncExitStack) -> Any:
        headers: dict[str, str] = self._headers()
        if self._connector.transport == "sse":
            return await stack.enter_async_context(
                sse_client(
                    self._connector.base_url, headers=headers, timeout=self._connector.timeout
                )
            )
        http_client = httpx2.AsyncClient(
            headers=headers,
            timeout=httpx2.Timeout(self._connector.timeout),
            follow_redirects=True,
            trust_env=False,
        )
        await stack.enter_async_context(http_client)
        return await stack.enter_async_context(
            streamable_http_client(self._connector.base_url, http_client=http_client)
        )

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = dict(self._operation.headers) if self._operation else {}
        request_id: str | None = request_id_context.get()
        if request_id:
            headers["X-Request-ID"] = request_id
        auth = self._connector.auth
        if isinstance(auth, TokenAuth):
            headers[auth.key_name] = auth.key_value
        elif isinstance(auth, BasicAuth):
            credentials: str = base64.b64encode(
                f"{auth.username}:{auth.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"
        return headers


async def _close_failed_attempt(attempt_stack: AsyncExitStack, raised: BaseException) -> Exception:
    cause: Exception | None = raised if isinstance(raised, Exception) else None
    try:
        await attempt_stack.aclose()
    except Exception as closing_error:
        cause = cause or closing_error
    task: asyncio.Task[Any] | None = asyncio.current_task()
    if cause is None or (task is not None and task.cancelling()):
        raise raised
    return cause


def root_causes(error: BaseException) -> str:
    if isinstance(error, BaseExceptionGroup):
        return "; ".join(root_causes(inner) for inner in error.exceptions)
    return f"{type(error).__name__}: {error}"
