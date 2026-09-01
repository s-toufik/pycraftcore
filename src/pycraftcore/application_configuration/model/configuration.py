from dataclasses import dataclass

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.model.connector import ConnectorTyping
from pycraftcore.application_configuration.model.operation import OperationTyping


@dataclass(frozen=True, slots=True)
class ApplicationConfiguration:
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: dict[ConnectorType, dict[str, ConnectorTyping]]
    operation: dict[str, OperationTyping]
