import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pycraftcore.runtime.python.adapter import ALLOWLIST, SafeCode


def test_parse_code_embeds_sorted_allowlist_and_repr_of_code():
    safe_code = SafeCode(code="result = 1 + 1", max_memory_mb=128)

    source = safe_code._parse_code()

    assert repr("result = 1 + 1") in source
    assert "_ALLOWED_IMPORTS = set(" in source
    assert str(sorted(ALLOWLIST)) in source
    assert "128" in source


@pytest.mark.asyncio
async def test_execute_runs_real_sandboxed_code_and_returns_json_result():
    safe_code = SafeCode(code="result = 2 + 2", code_timeout=10)

    output = await safe_code.execute()

    assert output.stderr == ""
    assert '"result": 4' in output.stdout


@pytest.mark.asyncio
async def test_execute_rejects_disallowed_imports():
    safe_code = SafeCode(code="import os", code_timeout=10)

    output = await safe_code.execute()

    assert output.stdout == ""
    assert "not allowed" in output.stderr


@pytest.mark.asyncio
async def test_execute_requires_result_variable():
    safe_code = SafeCode(code="x = 1", code_timeout=10)

    output = await safe_code.execute()

    assert output.stdout == ""
    assert "MissingResult" in output.stderr


@pytest.mark.asyncio
async def test_execute_returns_timeout_message_on_timeout_expired():
    safe_code = SafeCode(code="result = 1", code_timeout=5)
    fake_proc = MagicMock(kill=MagicMock(), wait=AsyncMock())

    with (
        patch(
            "pycraftcore.runtime.python.adapter.asyncio.create_subprocess_exec",
            AsyncMock(return_value=fake_proc),
        ),
        patch(
            "pycraftcore.runtime.python.adapter.asyncio.wait_for",
            side_effect=asyncio.TimeoutError,
        ),
    ):
        output = await safe_code.execute()

    assert output.stdout == ""
    assert "timed out after 5s" in output.stderr
    fake_proc.kill.assert_called_once()


@pytest.mark.asyncio
async def test_execute_returns_subprocess_error_message_on_unexpected_exception():
    safe_code = SafeCode(code="result = 1")

    with patch(
        "pycraftcore.runtime.python.adapter.asyncio.create_subprocess_exec",
        AsyncMock(side_effect=OSError("no such file")),
    ):
        output = await safe_code.execute()

    assert output.stdout == ""
    assert "Subprocess error" in output.stderr
    assert "no such file" in output.stderr


@pytest.mark.asyncio
async def test_execute_on_nonzero_returncode_embeds_stderr_text_not_returncode():
    """Regression test documenting a real bug: the non-zero-returncode branch formats
    `f"Process exited with code {stderr}."`, embedding stderr text where the
    numeric return code was almost certainly intended. Mirrors the same
    documented behavior in the agentic project's copy of this adapter."""
    safe_code = SafeCode(code="result = 1")
    fake_proc = MagicMock(
        returncode=1,
        communicate=AsyncMock(return_value=(b"", b"Traceback (most recent call last)")),
    )

    with patch(
        "pycraftcore.runtime.python.adapter.asyncio.create_subprocess_exec",
        AsyncMock(return_value=fake_proc),
    ):
        output = await safe_code.execute()

    assert output.stderr == "Process exited with code Traceback (most recent call last)."


@pytest.mark.asyncio
async def test_execute_always_removes_temporary_script(tmp_path):
    created_paths = []
    original_write = SafeCode._write_temporary_script

    def spying_write(runner_src):
        path = original_write(runner_src)
        created_paths.append(path)
        return path

    safe_code = SafeCode(code="result = 1")
    with patch.object(SafeCode, "_write_temporary_script", staticmethod(spying_write)):
        await safe_code.execute()

    assert created_paths
    assert not os.path.exists(created_paths[0])


@pytest.mark.asyncio
async def test_execute_removes_temporary_script_even_on_timeout(tmp_path):
    created_paths = []
    original_write = SafeCode._write_temporary_script

    def spying_write(runner_src):
        path = original_write(runner_src)
        created_paths.append(path)
        return path

    safe_code = SafeCode(code="result = 1", code_timeout=5)
    fake_proc = MagicMock(kill=MagicMock(), wait=AsyncMock())

    with (
        patch.object(SafeCode, "_write_temporary_script", staticmethod(spying_write)),
        patch(
            "pycraftcore.runtime.python.adapter.asyncio.create_subprocess_exec",
            AsyncMock(return_value=fake_proc),
        ),
        patch(
            "pycraftcore.runtime.python.adapter.asyncio.wait_for",
            side_effect=asyncio.TimeoutError,
        ),
    ):
        await safe_code.execute()

    assert created_paths
    assert not os.path.exists(created_paths[0])
