from string import Template
from typing import Protocol, runtime_checkable

from pycraftcore.runtime.schema.code_stdout import CodeStdout
from pycraftcore.runtime.schema.host_bridge import HostBridgeConfig


@runtime_checkable
class CodeFactory(Protocol):
    def __call__(
        self,
        code: str,
        code_template: Template | None = None,
        host_bridge: HostBridgeConfig | None = None,
    ) -> Code: ...


@runtime_checkable
class Code(Protocol):
    async def execute(self) -> CodeStdout: ...
