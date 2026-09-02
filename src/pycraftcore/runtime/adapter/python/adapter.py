import asyncio
import os
import subprocess
import sys
import tempfile
import textwrap
import traceback
from string import Template

from pycraftcore.runtime.configuration.schema import CodeStdout

_PYTHON_SAFE_BUILTINS: tuple[str, ...] = (
    "abs",
    "all",
    "any",
    "bool",
    "dict",
    "enumerate",
    "filter",
    "float",
    "int",
    "len",
    "list",
    "map",
    "max",
    "min",
    "pow",
    "print",
    "range",
    "reversed",
    "round",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
)

PYTHON_ALLOWLIST: frozenset[str] = frozenset(
    {
        "math",
        "statistics",
        "datetime",
        "re",
        "json",
        "collections",
        "itertools",
        "functools",
        "pandas",
        "numpy",
        "matplotlib",
    }
)

_PYTHON_RUNNER_TEMPLATE: Template = Template(
    textwrap.dedent("""\
import builtins
import json
import sys
import traceback

if sys.platform == "linux":
    import resource

    limit = $max_memory_mb * 1024 * 1024

    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))

sys.setrecursionlimit(500)

_ALLOWED_IMPORTS = set($allowlist)

_real_import = builtins.__import__


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".", 1)[0]
    if root not in _ALLOWED_IMPORTS:
        raise ImportError(f"Import '{root}' is not allowed.")
    return _real_import(name, globals, locals, fromlist, level)


_SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in $safe_builtins
}

_SAFE_BUILTINS["__import__"] = _safe_import
_SAFE_BUILTINS["__build_class__"] = builtins.__build_class__

_globals = {
    "__builtins__": _SAFE_BUILTINS,
    "__name__": "__sandbox__",
}

try:
    exec(compile($code, "<sandbox>", "exec"), _globals)
except Exception:
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

if "result" not in _globals:
    print(
        json.dumps({
            "error": "MissingResult",
            "message": "Assign the final output to a variable named 'result'."
        }),
        file=sys.stderr,
    )
    sys.exit(1)

print(
    json.dumps(
        {
            "__type__": type(_globals["result"]).__name__,
            "result": _globals["result"],
        },
        default=str,
    )
)
""")
)


class PythonSafeCode:
    def __init__(
        self,
        code: str,
        code_template: Template | None = None,
        code_timeout: int | None = 10,
        max_memory_mb: int | None = 256,
    ) -> None:
        self._code = code
        self._code_template = code_template or _PYTHON_RUNNER_TEMPLATE
        self._code_timeout = code_timeout
        self._max_memory_mb = max_memory_mb

    def _parse_code(self) -> str:
        return self._code_template.substitute(
            allowlist=repr(sorted(PYTHON_ALLOWLIST)),
            safe_builtins=repr(_PYTHON_SAFE_BUILTINS),
            code=repr(self._code),
            max_memory_mb=self._max_memory_mb,
        )

    @staticmethod
    def _build_environment() -> dict[str, str]:
        environment: dict[str, str] = {
            "PATH": os.environ.get("PATH", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHON_COLORS": "0",
        }
        if sys.platform == "win32":
            environment["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
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

        runner_src: str = self._parse_code()
        temporary_script_path = await self._create_temporary_script(runner_src)
        env = self._build_environment()
        try:
            return await self._execute_async(temporary_script_path, env)
        except NotImplementedError:
            return await asyncio.to_thread(self._execute_sync, temporary_script_path, env)
        except Exception as exception:
            traceback.print_exc()
            traceback_str: str = "".join(traceback.format_exception(exception))
            return CodeStdout(stdout="", stderr=f"Subprocess error: {traceback_str}")
        finally:
            await asyncio.to_thread(os.unlink, temporary_script_path)

    async def _execute_async(self, script_path: str, env: dict[str, str]) -> CodeStdout:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
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
