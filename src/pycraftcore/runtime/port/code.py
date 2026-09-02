from string import Template
from typing import Protocol, runtime_checkable

from pycraftcore.runtime.configuration.schema import CodeStdout


@runtime_checkable
class CodeFactory(Protocol):
    def __call__(self, code: str, code_template: Template | None = None) -> Code: ...


@runtime_checkable
class Code(Protocol):
    async def execute(self) -> CodeStdout: ...
