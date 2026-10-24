from dataclasses import dataclass

from pycraftcore.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.model.connector import ConnectorRegistry
from pycraftcore.application_configuration.model.operation import OperationRegistry
from pycraftcore.application_configuration.model.server import ServerRegistry
from pycraftcore.logger.enum.log_level import LogLevel


@dataclass(frozen=True, slots=True)
class ApplicationConfiguration:
    env: RunTypeEnvironment
    run: RunTypeApplication
    log: LogLevel
    server: ServerRegistry
    connector: ConnectorRegistry
    operation: OperationRegistry
