from pycraftcore.runtime.python.adapter import SafeCode
from pycraftcore.runtime.python.factory import SafeCodeFactory
from pycraftcore.runtime.python.schema import SafeCodeSettings


def test_default_settings_are_used_when_none_provided():
    factory = SafeCodeFactory()

    code = factory(code="result = 1")

    assert isinstance(code, SafeCode)
    assert code._code_timeout == 10
    assert code._max_memory_mb == 256


def test_explicit_settings_are_applied():
    factory = SafeCodeFactory(settings=SafeCodeSettings(code_timeout=42, max_memory_mb=64))

    code = factory(code="result = 1")

    assert code._code_timeout == 42
    assert code._max_memory_mb == 64


def test_code_template_is_forwarded():
    factory = SafeCodeFactory()

    code = factory(code="result = 1", code_template=None)

    assert code._code_template is not None
