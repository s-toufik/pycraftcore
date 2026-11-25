import inspect
from collections.abc import Callable
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from pycraftcore.mcp.exception.tool_call_error import ToolCallError
from pycraftcore.mcp.schema.served_tool import ServedTool


class SdkToolServer:
    def __init__(self, server: MCPServer) -> None:
        self._server = server

    def add_tool(self, tool: ServedTool) -> None:
        self._server.add_tool(
            _handler(tool), name=tool.name, description=tool.description, structured_output=True
        )

    def remove_tool(self, name: str) -> None:
        try:
            self._server.remove_tool(name)
        except ToolError:
            pass


def _handler(tool: ServedTool) -> Callable[..., Any]:
    async def handler(**arguments: Any) -> Any:
        try:
            return await tool.handler(arguments)
        except ToolCallError as failure:
            raise ToolError(str(failure)) from failure

    parameters: list[inspect.Parameter] = [
        inspect.Parameter(
            name,
            inspect.Parameter.KEYWORD_ONLY,
            annotation=Annotated[field.annotation, field],  # ty: ignore[invalid-type-form]
            default=inspect.Parameter.empty if field.is_required() else field.default,
        )
        for name, field in tool.input_model.model_fields.items()
    ]
    handler.__name__ = tool.name
    handler.__signature__ = inspect.Signature(  # ty: ignore[missing-attribute]
        parameters, return_annotation=tool.output_model
    )
    handler.__annotations__ = {parameter.name: parameter.annotation for parameter in parameters}
    handler.__annotations__["return"] = tool.output_model
    return handler
