import pytest
from mcp import Client
from opentelemetry import trace

from pycraftcore.mcp_sdk import create_server


def adding_server():
    server = create_server(name="toolbox", version="1.0.0")

    @server.tool()
    def add(a: int, b: int) -> int:
        return a + b

    return server


@pytest.mark.asyncio
async def test_a_call_joins_the_caller_s_trace_and_notifications_get_no_span(spans) -> None:
    with trace.get_tracer("test").start_as_current_span("agent run_tools") as caller:
        async with Client(adding_server()) as client:
            await client.call_tool("add", {"a": 1, "b": 2})

    names = [span.name for span in spans.get_finished_spans()]
    [call] = [span for span in spans.get_finished_spans() if span.name == "tools/call add"]
    assert call.context is not None
    assert call.context.trace_id == caller.get_span_context().trace_id
    assert not any(name.startswith("notifications/") for name in names)


def test_the_server_carries_its_name_version_and_instructions() -> None:
    server = create_server(name="toolbox-kitchen", version="1.3.0", instructions="Kitchen tools.")

    assert (server.name, server.version, server.instructions) == (
        "toolbox-kitchen",
        "1.3.0",
        "Kitchen tools.",
    )
