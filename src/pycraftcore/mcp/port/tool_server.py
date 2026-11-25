from typing import Protocol

from pycraftcore.mcp.schema.served_tool import ServedTool


class ToolServer(Protocol):
    def add_tool(self, tool: ServedTool) -> None: ...

    def remove_tool(self, name: str) -> None: ...
