import pytest

from pycraftcore.application_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model import (
    A2aOperation,
    ApiOperation,
    DatabaseOperation,
    FileOperation,
    McpOperation,
    OperationRegistry,
)
from pycraftcore.http.enum.http_method import HttpMethod
from tests.application_configuration.model.connectors import (
    a2a_connector,
    api_connector,
    database_connector,
    file_connector,
    mcp_connector,
)


def ask_operation(declared: OperationType = OperationType.api) -> ApiOperation:
    return ApiOperation(
        name="ask",
        type=declared,
        connector=api_connector(),
        endpoint="/ask",
        method=HttpMethod.POST,
        parameters={},
    )


def test_registry_returns_the_typed_operation_by_name():
    operation = ask_operation()

    assert OperationRegistry({"ask": operation}).api("ask") is operation


def test_registry_lookup_of_missing_operation_raises_key_error():
    with pytest.raises(KeyError):
        OperationRegistry().api("missing")


def test_registry_lookup_of_wrong_kind_raises_type_error():
    operation = FileOperation(
        name="export",
        type=OperationType.file,
        connector=file_connector(),
        action=FileOperationAction.write,
        parameters={},
    )
    registry = OperationRegistry({"export": operation})

    with pytest.raises(TypeError):
        registry.api("export")


def test_registry_rejects_an_operation_whose_declared_type_disagrees_with_its_class():
    with pytest.raises(TypeError):
        OperationRegistry({"ask": ask_operation(declared=OperationType.file)})


def test_the_registry_returns_database_a2a_and_mcp_operations_by_name():
    ask = A2aOperation(name="ask", type=OperationType.a2a, connector=a2a_connector(), parameters={})
    orders = DatabaseOperation(
        name="orders", type=OperationType.database, connector=database_connector(), database="shop"
    )
    kitchen = McpOperation(name="kitchen", type=OperationType.mcp, connector=mcp_connector())
    registry = OperationRegistry({"orders": orders, "ask": ask, "kitchen": kitchen})

    assert registry.database("orders") is orders
    assert registry.a2a("ask") is ask
    assert registry.mcp("kitchen") is kitchen
    with pytest.raises(TypeError):
        registry.database("ask")
