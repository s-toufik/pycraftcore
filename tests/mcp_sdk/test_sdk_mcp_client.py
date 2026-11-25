import asyncio
from contextlib import AsyncExitStack
from typing import Any

import pytest
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from pycraftcore.application_configuration.enum import ConnectorType, OperationType
from pycraftcore.application_configuration.model import McpConnector, McpOperation
from pycraftcore.authentication.model.basic_auth import BasicAuth
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.authentication.model.token_auth import TokenAuth
from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.mcp import CallResult, McpUnavailableException, RemoteTool
from pycraftcore.mcp_sdk import SdkMcpClient
from pycraftcore.mcp_sdk.sdk_mcp_client import root_causes


def connector(auth: Any = None, base_url: str = "http://127.0.0.1:9/mcp") -> McpConnector:
    return McpConnector(
        name="mongodb", type=ConnectorType.mcp, auth=auth or NoAuth(), base_url=base_url, timeout=1
    )


class FakeSession:
    def __init__(self, result: CallToolResult | None = None) -> None:
        self.result = result
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def list_tools(self) -> ListToolsResult:
        return ListToolsResult(
            tools=[Tool(name="find", description="Find.", input_schema={"type": "object"})]
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        self.calls.append((name, arguments))
        assert self.result is not None
        return self.result


def connected(session: FakeSession) -> SdkMcpClient:
    client = SdkMcpClient(connector())

    async def connect(_stack: AsyncExitStack) -> Any:
        return session

    client._connect = connect  # ty: ignore[invalid-assignment]
    return client


@pytest.mark.asyncio
async def test_the_listed_tools_are_remote_tools() -> None:
    tools = await connected(FakeSession()).list_tools()

    assert tools == [RemoteTool("find", "Find.", {"type": "object"}, None)]


@pytest.mark.asyncio
async def test_a_call_returns_its_text_its_structured_content_and_whether_it_failed() -> None:
    session = FakeSession(
        CallToolResult(
            content=[TextContent(type="text", text="a"), TextContent(type="text", text="b")],
            structured_content={"rows": 2},
            is_error=True,
        )
    )

    result = await connected(session).call_tool("find", {"limit": 2})

    assert result == CallResult(content=("a", "b"), structured={"rows": 2}, is_error=True)
    assert result.text == "a\nb"
    assert session.calls == [("find", {"limit": 2})]


@pytest.mark.asyncio
async def test_a_server_that_doesn_t_answer_is_unavailable_after_its_attempts() -> None:
    client = SdkMcpClient(connector(), max_attempts=2, initial_delay=0.01)

    with pytest.raises(McpUnavailableException, match="after 2 attempts"):
        await client.list_tools()

    current = asyncio.current_task()
    assert current is not None and current.cancelling() == 0


@pytest.mark.asyncio
async def test_a_cancel_from_outside_still_cancels_the_connection() -> None:
    client = SdkMcpClient(connector(), max_attempts=50, initial_delay=0.01, max_delay=0.01)
    task = asyncio.create_task(client.list_tools())
    await asyncio.sleep(0.05)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task


class FailingSession(FakeSession):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        raise ExceptionGroup(
            "task group",
            [ConnectionError("refused"), ExceptionGroup("inner", [ValueError("bad schema")])],
        )


@pytest.mark.asyncio
async def test_a_failure_inside_a_session_is_unavailable_and_names_every_root_cause() -> None:
    with pytest.raises(McpUnavailableException) as raised:
        await connected(FailingSession()).call_tool("find", {})

    assert str(raised.value) == (
        "MCP server at http://127.0.0.1:9/mcp failed: ConnectionError: refused; ValueError: bad schema"
    )


def test_root_causes_flattens_nested_exception_groups() -> None:
    group = ExceptionGroup(
        "outer", [ConnectionError("refused"), ExceptionGroup("inner", [ValueError("bad schema")])]
    )

    assert root_causes(group) == "ConnectionError: refused; ValueError: bad schema"
    assert root_causes(TimeoutError("slow")) == "TimeoutError: slow"


@pytest.mark.parametrize(
    ("auth", "expected"),
    [
        (TokenAuth(key_name="Authorization", key_value="Bearer t"), {"Authorization": "Bearer t"}),
        (BasicAuth(username="u", password="p"), {"Authorization": "Basic dTpw"}),
        (None, {}),
    ],
)
def test_the_headers_carry_the_auth_the_operation_s_headers_and_the_request_id(
    auth, expected
) -> None:
    operation = McpOperation(
        name="mongodb",
        type=OperationType.mcp,
        connector=connector(auth),
        headers={"X-Team": "kitchen"},
    )
    token = request_id_context.set("r1")
    try:
        headers = SdkMcpClient(connector(auth), operation)._headers()
    finally:
        request_id_context.reset(token)

    assert headers == {"X-Team": "kitchen", "X-Request-ID": "r1"} | expected
