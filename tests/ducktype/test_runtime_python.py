from pycraftcore.runtime.port.code import Code, CodeFactory
from pycraftcore.runtime.adapter.python.adapter import PythonSafeCode
from pycraftcore.runtime.adapter.python.factory import PythonSafeCodeFactory


def test_safe_code_factory_satisfies_code_factory():
    factory: CodeFactory = PythonSafeCodeFactory()

    assert isinstance(factory, CodeFactory)


def test_safe_code_satisfies_code():
    code: Code = PythonSafeCode(code="result = 1")

    assert isinstance(code, Code)
