import asyncio
import os
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pycraftcore.runtime.adapter.python.adapter import ALLOWLIST, SafeCode


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
async def test_execute_allows_defining_classes_in_sandboxed_code():
    safe_code = SafeCode(
        code=(
            "class Point:\n    def __init__(self, x):\n        self.x = x\nresult = Point(3).x\n"
        ),
        code_timeout=10,
    )

    output = await safe_code.execute()

    assert output.stderr == ""
    assert '"result": 3' in output.stdout


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
            "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
            AsyncMock(return_value=fake_proc),
        ),
        patch(
            "pycraftcore.runtime.adapter.python.adapter.asyncio.wait_for",
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
        "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
        AsyncMock(side_effect=OSError("no such file")),
    ):
        output = await safe_code.execute()

    assert output.stdout == ""
    assert "Subprocess error" in output.stderr
    assert "no such file" in output.stderr


@pytest.mark.asyncio
async def test_execute_on_nonzero_returncode_uses_stderr_text_when_present():
    safe_code = SafeCode(code="result = 1")
    fake_proc = MagicMock(
        returncode=1,
        communicate=AsyncMock(return_value=(b"", b"Traceback (most recent call last)")),
    )

    with patch(
        "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
        AsyncMock(return_value=fake_proc),
    ):
        output = await safe_code.execute()

    assert output.stderr == "Traceback (most recent call last)"


@pytest.mark.asyncio
async def test_execute_on_nonzero_returncode_falls_back_to_returncode_when_stderr_empty():
    safe_code = SafeCode(code="result = 1")
    fake_proc = MagicMock(
        returncode=7,
        communicate=AsyncMock(return_value=(b"", b"")),
    )

    with patch(
        "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
        AsyncMock(return_value=fake_proc),
    ):
        output = await safe_code.execute()

    assert output.stderr == "Process exited with code 7."


@pytest.mark.asyncio
async def test_execute_on_nonzero_returncode_preserves_partial_stdout():
    safe_code = SafeCode(code="result = 1")
    fake_proc = MagicMock(
        returncode=1,
        communicate=AsyncMock(return_value=(b"partial output", b"boom")),
    )

    with patch(
        "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
        AsyncMock(return_value=fake_proc),
    ):
        output = await safe_code.execute()

    assert output.stdout == "partial output"
    assert output.stderr == "boom"


def test_build_environment_does_not_leak_arbitrary_host_variables():
    with patch.dict(
        os.environ,
        {"PATH": "/usr/bin", "LANG": "en_US.UTF-8", "SECRET_TOKEN": "leak-me"},
    ):
        environment = SafeCode._build_environment()

    assert environment == {
        "PATH": "/usr/bin",
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHON_COLORS": "0",
    }
    assert "SECRET_TOKEN" not in environment


@pytest.mark.asyncio
async def test_execute_passes_isolated_environment_to_subprocess():
    safe_code = SafeCode(code="result = 1", code_timeout=10)
    fake_proc = MagicMock(
        returncode=0,
        communicate=AsyncMock(return_value=(b'{"result": 1}', b"")),
    )

    with (
        patch.dict(os.environ, {"SECRET_TOKEN": "leak-me"}),
        patch(
            "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
            AsyncMock(return_value=fake_proc),
        ) as create_subprocess_exec,
    ):
        await safe_code.execute()

    passed_env = create_subprocess_exec.call_args.kwargs["env"]
    assert "SECRET_TOKEN" not in passed_env


@pytest.mark.asyncio
async def test_execute_falls_back_to_sync_subprocess_when_event_loop_lacks_support():
    safe_code = SafeCode(code="result = 2 + 2", code_timeout=10)

    with patch(
        "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
        AsyncMock(side_effect=NotImplementedError("subprocess not supported")),
    ):
        output = await safe_code.execute()

    assert output.stderr == ""
    assert '"result": 4' in output.stdout


@pytest.mark.asyncio
async def test_execute_sync_fallback_does_not_swap_stdout_and_stderr():
    safe_code = SafeCode(code="result = 1", code_timeout=10)
    fake_completed_process = MagicMock(returncode=0, stdout=b'{"result": 1}', stderr=b"")

    with (
        patch(
            "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
            AsyncMock(side_effect=NotImplementedError()),
        ),
        patch(
            "pycraftcore.runtime.adapter.python.adapter.subprocess.run",
            return_value=fake_completed_process,
        ),
    ):
        output = await safe_code.execute()

    assert output.stdout == '{"result": 1}'
    assert output.stderr == ""


@pytest.mark.asyncio
async def test_execute_sync_fallback_on_nonzero_returncode_does_not_raise():
    safe_code = SafeCode(code="raise ValueError(1)", code_timeout=10)
    fake_completed_process = MagicMock(returncode=1, stdout=b"", stderr=b"Traceback: ValueError")

    with (
        patch(
            "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
            AsyncMock(side_effect=NotImplementedError()),
        ),
        patch(
            "pycraftcore.runtime.adapter.python.adapter.subprocess.run",
            return_value=fake_completed_process,
        ),
    ):
        output = await safe_code.execute()

    assert output.stdout == ""
    assert output.stderr == "Traceback: ValueError"


@pytest.mark.asyncio
async def test_execute_sync_fallback_returns_timeout_message_on_timeout_expired():
    safe_code = SafeCode(code="result = 1", code_timeout=5)

    with (
        patch(
            "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
            AsyncMock(side_effect=NotImplementedError()),
        ),
        patch(
            "pycraftcore.runtime.adapter.python.adapter.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="python", timeout=5),
        ),
    ):
        output = await safe_code.execute()

    assert output.stdout == ""
    assert "timed out after 5s" in output.stderr


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
            "pycraftcore.runtime.adapter.python.adapter.asyncio.create_subprocess_exec",
            AsyncMock(return_value=fake_proc),
        ),
        patch(
            "pycraftcore.runtime.adapter.python.adapter.asyncio.wait_for",
            side_effect=asyncio.TimeoutError,
        ),
    ):
        await safe_code.execute()

    assert created_paths
    assert not os.path.exists(created_paths[0])
