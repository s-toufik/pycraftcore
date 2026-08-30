from pydantic import BaseModel
from typing import Sequence

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.model.configuration import ApplicationConfiguration
from pycraftcore.application_configuration.model.connector import ConnectorTyping

from pycraftcore.application_configuration.model.cronjob import CronJob
from pycraftcore.application_configuration.model.operation import OperationTyping


class ApplicationConfigurationSchema(BaseModel):
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: dict[ConnectorType, dict[str, ConnectorTyping]]
    operation: dict[str, OperationTyping]
    cronjob: Sequence[CronJob]


class MapperDomainSchema:
    @staticmethod
    def map(app_configuration_schema: ApplicationConfigurationSchema) -> ApplicationConfiguration:
        return ApplicationConfiguration(**vars(app_configuration_schema))
