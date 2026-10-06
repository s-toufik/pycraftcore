import asyncio
import json
import secrets
from collections.abc import Iterable
from typing import Any

from pycraftcore.runtime.schema.host_bridge import HostBridgeConfig, HostBridgeHandler


class HostBridgeServer:
    HOST = "127.0.0.1"

    def __init__(
        self,
        handler: HostBridgeHandler,
        function_names: Iterable[str],
        max_calls: int = 200,
        call_timeout: float = 30.0,
    ) -> None:
        self._handler = handler
        self._function_names: tuple[str, ...] = tuple(function_names)
        self._max_calls = max_calls
        self._call_timeout = call_timeout
        self._token: str = secrets.token_hex(16)
        self._server: asyncio.Server | None = None
        self._port: int = 0

    @property
    def config(self) -> HostBridgeConfig:
        if self._server is None:
            raise RuntimeError("HostBridgeServer is not started.")

        return HostBridgeConfig(
            host=self.HOST,
            port=self._port,
            token=self._token,
            function_names=self._function_names,
        )

    async def __aenter__(self) -> HostBridgeServer:
        self._server = await asyncio.start_server(self._handle, self.HOST, 0)
        self._port = self._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        calls = 0

        try:
            while line := await reader.readline():
                calls += 1
                over_quota: bool = calls > self._max_calls

                response: dict[str, Any] = (
                    _failure("Call quota exceeded.") if over_quota else await self._respond(line)
                )

                writer.write(json.dumps(response, default=str).encode("utf-8") + b"\n")
                await writer.drain()

                if over_quota:
                    break

        except ConnectionError:
            pass

        except asyncio.CancelledError:
            raise

        finally:
            writer.close()

    async def _respond(self, line: bytes) -> dict[str, Any]:
        try:
            request: Any = json.loads(line)
        except json.JSONDecodeError:
            return _failure("Malformed request.")

        if not isinstance(request, dict) or not secrets.compare_digest(
            str(request.get("token", "")), self._token
        ):
            return _failure("Unauthorized.")

        name: Any = request.get("function")
        if name not in self._function_names:
            return _failure(f"Function {name!r} is not available in the sandbox.")

        arguments: Any = request.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _failure("Arguments must be passed as keywords.")

        try:
            output: Any = await asyncio.wait_for(self._handler(name, arguments), self._call_timeout)
        except TimeoutError:
            return _failure(f"Call to {name!r} timed out after {self._call_timeout}s.")
        except Exception as exception:
            return _failure(str(exception) or type(exception).__name__)

        return {"ok": True, "output": output}


def _failure(error: str) -> dict[str, Any]:
    return {"ok": False, "error": error}
