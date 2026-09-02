from string import Template

from pycraftcore.runtime.port.code import Code
from pycraftcore.runtime.adapter.python.adapter import SafeCode
from pycraftcore.runtime.configuration.schema import SafeCodeSettings


class SafeCodeFactory:
    def __init__(self, settings: SafeCodeSettings | None = None) -> None:
        self._settings = settings or SafeCodeSettings()

    def __call__(self, code: str, code_template: Template | None = None) -> Code:
        return SafeCode(
            code=code,
            code_template=code_template,
            code_timeout=self._settings.code_timeout,
            max_memory_mb=self._settings.max_memory_mb,
        )
