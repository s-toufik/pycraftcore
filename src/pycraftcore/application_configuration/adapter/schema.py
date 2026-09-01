from pydantic import BaseModel

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from pycraftcore.application_configuration.model.connector import (
    ConnectorRegistry,
    ConnectorTyping,
)
from pycraftcore.application_configuration.model.operation import (
    OperationRegistry,
    OperationTyping,
)


class ApplicationConfigurationSchema(BaseModel):
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: dict[ConnectorType, dict[str, ConnectorTyping]]
    operation: dict[str, OperationTyping]


class MapperDomainSchema:
    @staticmethod
    def map(
        app_configuration_schema: ApplicationConfigurationSchema,
    ) -> ApplicationConfiguration:
        return ApplicationConfiguration(
            env=app_configuration_schema.env,
            run=app_configuration_schema.run,
            connector=ConnectorRegistry(app_configuration_schema.connector),
            operation=OperationRegistry(app_configuration_schema.operation),
        )
