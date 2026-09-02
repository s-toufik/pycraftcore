from pycraftcore.runtime.port.code import Code, CodeFactory
from pycraftcore.runtime.adapter.python.adapter import SafeCode
from pycraftcore.runtime.adapter.python.factory import SafeCodeFactory


def test_safe_code_factory_satisfies_code_factory():
    factory: CodeFactory = SafeCodeFactory()

    assert isinstance(factory, CodeFactory)


def test_safe_code_satisfies_code():
    code: Code = SafeCode(code="result = 1")

    assert isinstance(code, Code)
