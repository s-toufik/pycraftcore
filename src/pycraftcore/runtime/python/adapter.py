import asyncio
import os
import sys
import tempfile
import textwrap
from string import Template
from typing import Optional

from pycraftcore.runtime.python.schema import CodeStdout

_SAFE_BUILTINS: tuple[str, ...] = (
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

ALLOWLIST: frozenset[str] = frozenset(
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

_RUNNER_TEMPLATE: Template = Template(
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

_globals = {
    "__builtins__": _SAFE_BUILTINS,
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


class SafeCode:
    def __init__(
        self,
        code: str,
        code_template: Optional[Template] = None,
        code_timeout: Optional[int] = 10,
        max_memory_mb: Optional[int] = 256,
    ) -> None:
        self._code = code
        self._code_template = code_template or _RUNNER_TEMPLATE
        self._code_timeout = code_timeout
        self._max_memory_mb = max_memory_mb

    def _parse_code(self) -> str:
        return self._code_template.substitute(
            allowlist=repr(sorted(ALLOWLIST)),
            safe_builtins=repr(_SAFE_BUILTINS),
            code=repr(self._code),
            max_memory_mb=self._max_memory_mb,
        )

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
        env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHON_COLORS": "0",
        }
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                temporary_script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=self._code_timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return CodeStdout(
                    stdout="", stderr=f"Execution timed out after {self._code_timeout}s."
                )
        except Exception as exc:
            return CodeStdout(stdout="", stderr=f"Subprocess error: {exc}")
        finally:
            await asyncio.to_thread(os.unlink, temporary_script_path)

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return CodeStdout(stdout="", stderr=f"Process exited with code {stderr}.")
        return CodeStdout(stdout=stdout.strip() or "", stderr=stderr.strip() or "")
