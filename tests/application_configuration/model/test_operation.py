import pytest

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model.connector import (
    A2aConnector,
    ApiConnector,
    DatabaseConnector,
    FileConnector,
)
from pycraftcore.application_configuration.model.operation import (
    A2aOperation,
    ApiOperation,
    DatabaseOperation,
    FileOperation,
    OperationRegistry,
)
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.http.enum.http_method import HttpMethod


def make_api_connector() -> ApiConnector:
    return ApiConnector(
        name="llm",
        type=ConnectorType.api,
        auth=NoAuth(type=AuthType.none),
        base_url="https://api.test.com",
        timeout=30,
        retry=3,
    )


def make_file_connector() -> FileConnector:
    return FileConnector(
        name="files",
        type=ConnectorType.file,
        auth=NoAuth(type=AuthType.none),
        base_path="/var/files",
    )


def test_api_operation_holds_endpoint_and_method():
    operation = ApiOperation(
        name="ask",
        type=OperationType.api,
        connector=make_api_connector(),
        endpoint="/ask",
        method=HttpMethod.POST,
        parameters={"query": "str"},
    )

    assert operation.endpoint == "/ask"
    assert operation.method == HttpMethod.POST
    assert operation.parameters == {"query": "str"}


def test_file_operation_holds_action_and_parameters():
    operation = FileOperation(
        name="export",
        type=OperationType.file,
        connector=make_file_connector(),
        action=FileOperationAction.write,
        parameters={"path": "str"},
    )

    assert operation.action == FileOperationAction.write
    assert operation.parameters == {"path": "str"}


def test_registry_returns_the_typed_operation_by_name():
    operation = ApiOperation(
        name="ask",
        type=OperationType.api,
        connector=make_api_connector(),
        endpoint="/ask",
        method=HttpMethod.POST,
        parameters={},
    )
    registry = OperationRegistry({"ask": operation})

    assert registry.api("ask") is operation


def test_registry_lookup_of_missing_operation_raises_key_error():
    registry = OperationRegistry()

    with pytest.raises(KeyError):
        registry.api("missing")


def test_registry_lookup_of_wrong_kind_raises_type_error():
    operation = FileOperation(
        name="export",
        type=OperationType.file,
        connector=make_file_connector(),
        action=FileOperationAction.write,
        parameters={},
    )
    registry = OperationRegistry({"export": operation})

    with pytest.raises(TypeError):
        registry.api("export")


def test_registry_rejects_an_operation_whose_declared_type_disagrees_with_its_class():
    operation = ApiOperation(
        name="ask",
        type=OperationType.file,
        connector=make_api_connector(),
        endpoint="/ask",
        method=HttpMethod.POST,
        parameters={},
    )

    with pytest.raises(TypeError):
        OperationRegistry({"ask": operation})


def make_database_connector() -> DatabaseConnector:
    return DatabaseConnector(
        name="pg",
        type=ConnectorType.database,
        auth=NoAuth(type=AuthType.none),
        engine="postgresql",
        host="db",
        port=5432,
    )


def make_database_operation(**overrides) -> DatabaseOperation:
    values = dict(
        name="orders",
        type=OperationType.database,
        connector=make_database_connector(),
        database="shop",
    )
    values.update(overrides)
    return DatabaseOperation(**values)


def test_a_database_operation_names_its_database_and_has_no_collections_or_ttl_by_default():
    operation = make_database_operation()

    assert operation.database == "shop"
    assert (operation.collections, operation.ttl, operation.parameters) == ({}, None, {})


def test_a_collection_is_found_by_its_role():
    operation = make_database_operation(collections={"events": "order_events"})

    assert operation.collection("events") == "order_events"


def test_a_missing_collection_names_the_operation_and_the_role():
    with pytest.raises(KeyError, match="'orders' has no collection 'events'"):
        make_database_operation().collection("events")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [({"database": " "}, "needs a database"), ({"ttl": -1}, "ttl must be 0 or more")],
)
def test_a_database_operation_that_cannot_work_is_refused(overrides, message):
    with pytest.raises(ValueError, match=message):
        make_database_operation(**overrides)


def test_the_registry_returns_database_and_a2a_operations_by_name():
    agent = A2aConnector(
        name="agent",
        type=ConnectorType.a2a,
        auth=NoAuth(type=AuthType.none),
        base_url="http://agent/a2a",
        timeout=60,
    )
    ask = A2aOperation(name="ask", type=OperationType.a2a, connector=agent, parameters={})
    orders = make_database_operation()
    registry = OperationRegistry({"orders": orders, "ask": ask})

    assert registry.database("orders") is orders
    assert registry.a2a("ask") is ask
    with pytest.raises(TypeError):
        registry.database("ask")
