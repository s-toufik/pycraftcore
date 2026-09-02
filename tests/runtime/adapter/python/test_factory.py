from typing import cast

from pycraftcore.runtime.adapter.python.adapter import PythonSafeCode
from pycraftcore.runtime.adapter.python.factory import PythonSafeCodeFactory
from pycraftcore.runtime.configuration.schema import SafeCodeSettings


def test_default_settings_are_used_when_none_provided():
    factory = PythonSafeCodeFactory()

    code = factory(code="result = 1")

    assert isinstance(code, PythonSafeCode)
    assert code._code_timeout == 10
    assert code._max_memory_mb == 256


def test_explicit_settings_are_applied():
    factory = PythonSafeCodeFactory(settings=SafeCodeSettings(code_timeout=42, max_memory_mb=64))

    code = cast(PythonSafeCode, factory(code="result = 1"))

    assert code._code_timeout == 42
    assert code._max_memory_mb == 64


def test_code_template_is_forwarded():
    factory = PythonSafeCodeFactory()

    code = cast(PythonSafeCode, factory(code="result = 1"))

    assert code._code_template is not None
