from typing import Any, Protocol

from pycraftcore.mcp.schema.call_result import CallResult
from pycraftcore.mcp.schema.remote_tool import RemoteTool


class McpClient(Protocol):
    async def list_tools(self) -> list[RemoteTool]: ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallResult: ...
