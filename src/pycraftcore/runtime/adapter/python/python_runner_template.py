import textwrap
from string import Template


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
import os
import socket
import sys

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

# Optional vault directory. When set, file access is confined to it; when None,
# sandbox has no filesystem access at all.
VAULT = $vault
_real_open = builtins.open

def _resolve_in_vault(path: str) -> str:
    vault_root = os.path.normcase(os.path.realpath(VAULT))
    candidate = path if os.path.isabs(path) else os.path.join(VAULT, path)
    resolved = os.path.realpath(candidate)

    try:
        common = os.path.commonpath((os.path.normcase(resolved), vault_root))
    except ValueError:
        common = None
    if common != vault_root:
        raise PermissionError(f"Path {path!r} is outside the vault.")

    return resolved


def _safe_open(file, mode="r", *args, **kwargs):
    if VAULT is None:
        raise PermissionError("File access is not allowed: no vault is configured.")

    return _real_open(
        _resolve_in_vault(os.fspath(file)),
        mode,
        *args,
        **kwargs,
    )


# Optional host bridge. When configured, each name in
# "bridge_functions" becomes a function that round-trips to the
# parent process over an authenticated loopback socket and returns the
# host's output already decoded into a native Python value (whatever
# JSON value the host placed under "output" in its response).
_BRIDGE_FUNCTIONS = $bridge_functions
_BRIDGE_HOST = os.environ.get("SANDBOX_BRIDGE_HOST")
_BRIDGE_PORT = os.environ.get("SANDBOX_BRIDGE_PORT")
_BRIDGE_TOKEN = os.environ.get("SANDBOX_BRIDGE_TOKEN")

class _HostBridge:
    def __init__(self):
        self._socket = None
        self._buffer = b""

    def _connection(self):
        if self._socket is None:
            self._socket = socket.create_connection((_BRIDGE_HOST, int(_BRIDGE_PORT)))
        return self._socket

    def call(self, tool, arguments):
        request = json.dumps(
            {
                "token": _BRIDGE_TOKEN,
                "tool": tool,
                "arguments": arguments,
            }
        )

        connection = self._connection()

        connection.sendall(
            request.encode("utf-8") + b"\\n"
        )

        response = json.loads(
            self._readline(connection)
        )

        if response.get("error"):
            raise RuntimeError(response["error"])

        return response.get("output")

    def _readline(self, connection):
        while b"\\n" not in self._buffer:
            chunk = connection.recv(65536)

            if not chunk:
                raise RuntimeError(
                    "Host bridge connection closed."
                )

            self._buffer += chunk

        line, _, self._buffer = self._buffer.partition(b"\\n")

        return line.decode("utf-8")


_bridge = _HostBridge()


def _make_bridge_proxy(tool):
    def _proxy(**arguments):
        return _bridge.call(tool, arguments)

    return _proxy


_BRIDGE_PROXIES = {
    name: _make_bridge_proxy(name)
    for name in _BRIDGE_FUNCTIONS
}


_SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in $safe_builtins
}

_SAFE_BUILTINS["__import__"] = _safe_import
_SAFE_BUILTINS["__build_class__"] = builtins.__build_class__
_SAFE_BUILTINS["open"] = _safe_open

_globals = {
    "__builtins__": _SAFE_BUILTINS,
    "__name__": "__sandbox__",
    "VAULT": VAULT,
    **_BRIDGE_PROXIES
}

try:
    exec(compile($code, "<sandbox>", "exec"), _globals)
except Exception as exc:
    print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    sys.exit(1)

if "result" not in _globals:
    print("Assign the final output to a variable named 'result'.", file=sys.stderr)
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
