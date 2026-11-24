from dataclasses import dataclass
from typing import Any

from pycraftcore.application_configuration.model.connector.api_connector import ApiConnector
from pycraftcore.application_configuration.model.operation.base_operation import BaseOperation
from pycraftcore.http.enum.http_method import HttpMethod


@dataclass(slots=True)
class ApiOperation(BaseOperation):
    connector: ApiConnector
    endpoint: str
    method: HttpMethod
    parameters: dict[str, Any]
