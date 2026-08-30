from typing import Sequence
from dataclasses import dataclass

from pycraftcore.app_configuration.enum.connector_type import ConnectorType
from pycraftcore.app_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.app_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.app_configuration.model.connector import ConnectorTyping
from pycraftcore.app_configuration.model.cronjob import CronJob
from pycraftcore.app_configuration.model.operation import OperationTyping


@dataclass(frozen=True, slots=True)
class AppConfiguration:
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: dict[ConnectorType, dict[str, ConnectorTyping]]
    operation: dict[str, OperationTyping]
    cronjob: Sequence[CronJob]
