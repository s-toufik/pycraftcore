from dataclasses import dataclass
from typing import Any

from pycraftcore.application_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.application_configuration.model.connector.file_connector import FileConnector
from pycraftcore.application_configuration.model.operation.base_operation import BaseOperation


@dataclass(slots=True)
class FileOperation(BaseOperation):
    connector: FileConnector
    action: FileOperationAction
    parameters: dict[str, Any]
