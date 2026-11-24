from dataclasses import dataclass
from typing import Any

from pycraftcore.application_configuration.model.connector.a2a_connector import A2aConnector
from pycraftcore.application_configuration.model.operation.base_operation import BaseOperation


@dataclass(slots=True)
class A2aOperation(BaseOperation):
    connector: A2aConnector
    parameters: dict[str, Any]
