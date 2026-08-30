from dataclasses import dataclass
from typing import Union, List

from pycraftcore.app_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.app_configuration.model.connector import ConnectorTyping
from pycraftcore.http.enum.http_method import HttpMethod

ParamType = Union[str, List[str]]


@dataclass(slots=True)
class BaseOperation:
    name: str
    connector: ConnectorTyping


@dataclass(slots=True)
class ApiOperation(BaseOperation):
    endpoint: str
    method: HttpMethod
    parameters: dict[str, ParamType]


@dataclass(slots=True)
class FileOperation(BaseOperation):
    action: FileOperationAction
    parameters: dict[str, ParamType]


OperationTyping = Union[FileOperation, ApiOperation]
