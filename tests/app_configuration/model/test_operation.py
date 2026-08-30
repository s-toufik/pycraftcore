from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.file_operation_action import FileOperationAction
from pycraftcore.application_configuration.model.connector import ApiConnector
from pycraftcore.application_configuration.model.operation import ApiOperation, FileOperation
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


def test_api_operation_holds_endpoint_and_method():
    operation = ApiOperation(
        name="ask",
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
        connector=make_api_connector(),
        action=FileOperationAction.write,
        parameters={"path": "str"},
    )

    assert operation.action == FileOperationAction.write
    assert operation.parameters == {"path": "str"}
