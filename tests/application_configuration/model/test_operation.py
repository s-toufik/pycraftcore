import pytest

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model.connector import ApiConnector, FileConnector
from pycraftcore.application_configuration.model.operation import (
    ApiOperation,
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
