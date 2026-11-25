from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from pycraftcore.mcp import ServedTool, ToolCallError
from pycraftcore.mcp_sdk import SdkToolServer, create_server


class EchoInput(BaseModel):
    text: str
    times: int = 1


class EchoOutput(BaseModel):
    echoed: str


def echo(handler=None) -> ServedTool:
    async def repeat(arguments: dict[str, Any]) -> dict[str, Any]:
        return {"echoed": arguments["text"] * arguments.get("times", 1)}

    return ServedTool("echo", "Repeat text.", EchoInput, EchoOutput, handler or repeat)


def served(tool: ServedTool):
    server = create_server(name="test", version="1.0.0")
    SdkToolServer(server).add_tool(tool)
    return server


@pytest.mark.asyncio
async def test_the_schemas_and_description_come_from_the_served_tool() -> None:
    [listed] = await served(echo()).list_tools()

    assert (listed.name, listed.description) == ("echo", "Repeat text.")
    assert listed.input_schema["properties"].keys() == EchoInput.model_fields.keys()
    assert listed.input_schema["required"] == ["text"]
    assert listed.output_schema == EchoOutput.model_json_schema()


@pytest.mark.asyncio
async def test_the_handler_gets_the_arguments_and_its_answer_is_the_structured_content() -> None:
    result = await served(echo()).call_tool("echo", {"text": "ab", "times": 2})

    assert result.structured_content == {"echoed": "abab"}
    assert not result.is_error


@pytest.mark.asyncio
async def test_a_tool_call_error_reaches_the_client_with_its_message() -> None:
    async def fail(_: dict[str, Any]) -> Any:
        raise ToolCallError("File not found.")

    with pytest.raises(ToolError, match="^Error executing tool echo: File not found.$"):
        await served(echo(fail)).call_tool("echo", {"text": "a"})


@pytest.mark.asyncio
async def test_a_removed_tool_is_no_longer_listed_and_removing_it_twice_is_fine() -> None:
    server = create_server(name="test", version="1.0.0")
    tools = SdkToolServer(server)
    tools.add_tool(echo())

    tools.remove_tool("echo")
    tools.remove_tool("echo")

    assert await server.list_tools() == []
