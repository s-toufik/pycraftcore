from pydantic import BaseModel
from typing import Sequence

from pycraftcore.app_configuration.enum.connector_type import ConnectorType
from pycraftcore.app_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.app_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.app_configuration.model.configuration import AppConfiguration
from pycraftcore.app_configuration.model.connector import ConnectorTyping

from pycraftcore.app_configuration.model.cronjob import CronJob
from pycraftcore.app_configuration.model.operation import OperationTyping


class AppConfigurationSchema(BaseModel):
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: dict[ConnectorType, dict[str, ConnectorTyping]]
    operation: dict[str, OperationTyping]
    cronjob: Sequence[CronJob]


class MapperDomainSchema:
    @staticmethod
    def map(app_configuration_schema: AppConfigurationSchema) -> AppConfiguration:
        return AppConfiguration(**vars(app_configuration_schema))
