from dataclasses import dataclass

from pycraftcore.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.model.connector import ConnectorRegistry
from pycraftcore.application_configuration.model.operation import OperationRegistry


@dataclass(frozen=True, slots=True)
class ApplicationConfiguration:
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: ConnectorRegistry
    operation: OperationRegistry
