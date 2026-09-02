from string import Template

from pycraftcore.runtime.port.code import Code
from pycraftcore.runtime.adapter.python.adapter import PythonSafeCode
from pycraftcore.runtime.configuration.schema import SafeCodeSettings


class PythonSafeCodeFactory:
    def __init__(self, settings: SafeCodeSettings | None = None) -> None:
        self._settings = settings or SafeCodeSettings()

    def __call__(self, code: str, code_template: Template | None = None) -> Code:
        return PythonSafeCode(
            code=code,
            code_template=code_template,
            code_timeout=self._settings.code_timeout,
            max_memory_mb=self._settings.max_memory_mb,
        )
