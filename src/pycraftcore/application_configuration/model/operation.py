from dataclasses import dataclass
from typing import Any

from pycraftcore.application_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.application_configuration.model.connector import ConnectorTyping
from pycraftcore.http.enum.http_method import HttpMethod


@dataclass(slots=True)
class BaseOperation:
    name: str
    connector: ConnectorTyping


@dataclass(slots=True)
class ApiOperation(BaseOperation):
    endpoint: str
    method: HttpMethod
    parameters: dict[str, Any]


@dataclass(slots=True)
class FileOperation(BaseOperation):
    action: FileOperationAction
    parameters: dict[str, Any]


OperationTyping = FileOperation | ApiOperation
