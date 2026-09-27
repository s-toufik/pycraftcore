import asyncio
import json
from typing import Any

import pytest

from pycraftcore.runtime.adapter.python.adapter import PythonSafeCode
from pycraftcore.runtime.adapter.python.host_bridge_server import HostBridgeServer
from pycraftcore.runtime.schema.code_result import CodeResult


async def _echo(name: str, arguments: dict[str, Any]) -> Any:
    if arguments.get("fail"):
        raise ValueError("File not found.")
    return {"function": name, "arguments": arguments}


async def _call(server: HostBridgeServer, *requests: dict[str, Any]) -> list[dict[str, Any]]:
    config = server.config
    reader, writer = await asyncio.open_connection(config.host, config.port)
    responses: list[dict[str, Any]] = []
    try:
        for request in requests:
            writer.write(json.dumps(request).encode("utf-8") + b"\n")
            await writer.drain()
            responses.append(json.loads(await reader.readline()))
    finally:
        writer.close()
    return responses


def _request(server: HostBridgeServer, function: str, **arguments: Any) -> dict[str, Any]:
    return {"token": server.config.token, "function": function, "arguments": arguments}


def test_config_before_start_raises():
    with pytest.raises(RuntimeError):
        _ = HostBridgeServer(_echo, ("echo",)).config


@pytest.mark.asyncio
async def test_successful_call_returns_handler_output():
    async with HostBridgeServer(_echo, ("echo",)) as server:
        [response] = await _call(server, _request(server, "echo", x=1))

    assert response == {"ok": True, "output": {"function": "echo", "arguments": {"x": 1}}}


@pytest.mark.asyncio
async def test_handler_exception_message_is_returned_as_error():
    async with HostBridgeServer(_echo, ("echo",)) as server:
        [response] = await _call(server, _request(server, "echo", fail=True))

    assert response == {"ok": False, "error": "File not found."}


@pytest.mark.asyncio
async def test_wrong_token_is_rejected():
    async with HostBridgeServer(_echo, ("echo",)) as server:
        [response] = await _call(server, {"token": "nope", "function": "echo", "arguments": {}})

    assert response == {"ok": False, "error": "Unauthorized."}


@pytest.mark.asyncio
async def test_unknown_function_is_rejected():
    async with HostBridgeServer(_echo, ("echo",)) as server:
        [response] = await _call(server, _request(server, "other"))

    assert response == {"ok": False, "error": "Function 'other' is not available in the sandbox."}


@pytest.mark.asyncio
async def test_calls_over_quota_are_rejected():
    async with HostBridgeServer(_echo, ("echo",), max_calls=1) as server:
        first, second = await _call(server, _request(server, "echo"), _request(server, "echo"))

    assert first["ok"] is True
    assert second == {"ok": False, "error": "Call quota exceeded."}


@pytest.mark.asyncio
async def test_slow_handler_times_out():
    async def slow(name: str, arguments: dict[str, Any]) -> Any:
        await asyncio.sleep(1)

    async with HostBridgeServer(slow, ("slow",), call_timeout=0.05) as server:
        [response] = await _call(server, _request(server, "slow"))

    assert response == {"ok": False, "error": "Call to 'slow' timed out after 0.05s."}


@pytest.mark.asyncio
async def test_sandboxed_code_calls_bridge_functions_and_catches_tool_error():
    code = (
        "ok = echo(x=1)\n"
        "try:\n"
        "    echo(fail=True)\n"
        "except ToolError as error:\n"
        "    message = str(error)\n"
        "result = {'ok': ok, 'message': message}\n"
    )

    async with HostBridgeServer(_echo, ("echo",)) as server:
        output = await PythonSafeCode(
            code=code, code_timeout=10, host_bridge_config=server.config
        ).execute()

    assert output.stderr == ""
    assert CodeResult.from_stdout(output.stdout).value == {
        "ok": {"function": "echo", "arguments": {"x": 1}},
        "message": "File not found.",
    }


@pytest.mark.asyncio
async def test_uncaught_tool_error_is_reported_on_stderr():
    async with HostBridgeServer(_echo, ("echo",)) as server:
        output = await PythonSafeCode(
            code="echo(fail=True)", code_timeout=10, host_bridge_config=server.config
        ).execute()

    assert output.stderr == "ToolError: File not found."
