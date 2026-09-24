import asyncio
import os
import subprocess
import sys
import tempfile
from string import Template

from pycraftcore.runtime.adapter.python.python_runner_template import (
    PYTHON_ALLOWLIST,
    _PYTHON_SAFE_BUILTINS,
    _PYTHON_RUNNER_TEMPLATE,
)
from pycraftcore.runtime.schema.code_stdout import CodeStdout
from pycraftcore.runtime.schema.host_bridge import HostBridgeConfig


class PythonSafeCode:
    def __init__(
        self,
        code: str,
        code_template: Template | None = None,
        code_timeout: int | None = 10,
        max_memory_mb: int | None = 256,
        vault_path: str | None = None,
        host_bridge_config: HostBridgeConfig | None = None,
    ) -> None:
        self._code = code
        self._code_template = code_template or _PYTHON_RUNNER_TEMPLATE
        self._code_timeout = code_timeout
        self._max_memory_mb = max_memory_mb
        self._vault_path = os.path.realpath(vault_path) if vault_path else None
        self._host_bridge_config = host_bridge_config

    def _parse_code(self) -> str:
        function_names: tuple[str, ...] = (
            self._host_bridge_config.function_names if self._host_bridge_config else ()
        )

        return self._code_template.substitute(
            allowlist=repr(sorted(PYTHON_ALLOWLIST)),
            safe_builtins=repr(_PYTHON_SAFE_BUILTINS),
            code=repr(self._code),
            max_memory_mb=self._max_memory_mb,
            vault=repr(self._vault_path),
            bridge_functions=repr(list(function_names)),
        )

    def _build_environment(self) -> dict[str, str]:
        environment: dict[str, str] = {
            "PATH": os.environ.get("PATH", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHON_COLORS": "0",
            # Headless plotting and single-threaded BLAS keep matplotlib/numpy
            # working without a display and within the memory limit.
            "MPLBACKEND": "Agg",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        }
        if sys.platform == "win32":
            environment["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
        if self._host_bridge_config is not None:
            environment["SANDBOX_BRIDGE_HOST"] = self._host_bridge_config.host
            environment["SANDBOX_BRIDGE_PORT"] = str(self._host_bridge_config.port)
            environment["SANDBOX_BRIDGE_TOKEN"] = self._host_bridge_config.token

        return environment

    @staticmethod
    def _write_temporary_script(runner_src: str) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as temporary_script:
            temporary_script.write(runner_src)
            temporary_script_path = temporary_script.name

        return temporary_script_path

    @classmethod
    async def _create_temporary_script(cls, runner_src: str) -> str:
        return await asyncio.to_thread(cls._write_temporary_script, runner_src)

    async def execute(self) -> CodeStdout:

        if self._vault_path is not None and not os.path.isdir(self._vault_path):
            return CodeStdout(
                stdout="",
                stderr=f"Subprocess error: vault directory does not exist {self._vault_path}",
            )

        runner_src: str = self._parse_code()
        temporary_script_path = await self._create_temporary_script(runner_src)
        env = self._build_environment()
        try:
            return await self._execute_async(temporary_script_path, env)
        except NotImplementedError:
            return await asyncio.to_thread(self._execute_sync, temporary_script_path, env)
        except Exception as exception:
            return CodeStdout(stdout="", stderr=f"Subprocess error: {exception}")
        finally:
            await asyncio.to_thread(os.unlink, temporary_script_path)

    async def _execute_async(self, script_path: str, env: dict[str, str]) -> CodeStdout:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=self._vault_path,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=self._code_timeout
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return CodeStdout(stdout="", stderr=f"Execution timed out after {self._code_timeout}s.")

        return self._build_result(proc.returncode, stderr_bytes, stdout_bytes)

    def _execute_sync(self, script_path: str, env: dict[str, str]) -> CodeStdout:
        try:
            proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                timeout=self._code_timeout,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return CodeStdout(stdout="", stderr=f"Execution timed out after {self._code_timeout}s.")

        return self._build_result(proc.returncode, proc.stderr, proc.stdout)

    @staticmethod
    def _build_result(
        return_code: int | None, stderr_bytes: bytes, stdout_bytes: bytes
    ) -> CodeStdout:
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        if return_code != 0:
            return CodeStdout(
                stdout=stdout.strip(),
                stderr=stderr.strip() or f"Process exited with code {return_code}.",
            )
        return CodeStdout(stdout=stdout.strip(), stderr=stderr.strip())
