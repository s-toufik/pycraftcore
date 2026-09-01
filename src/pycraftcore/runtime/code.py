from string import Template
from typing import Protocol

from pycraftcore.runtime.python.schema import CodeStdout


class CodeFactory(Protocol):
    def __call__(self, code: str, code_template: Template | None = None) -> Code: ...


class Code(Protocol):
    async def execute(self) -> CodeStdout: ...
