from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model import ApiOperation
from pycraftcore.http.enum.http_method import HttpMethod
from tests.application_configuration.model.connectors import api_connector


def test_api_operation_holds_endpoint_and_method():
    operation = ApiOperation(
        name="ask",
        type=OperationType.api,
        connector=api_connector(),
        endpoint="/ask",
        method=HttpMethod.POST,
        parameters={"query": "str"},
    )

    assert operation.endpoint == "/ask"
    assert operation.method == HttpMethod.POST
    assert operation.parameters == {"query": "str"}
