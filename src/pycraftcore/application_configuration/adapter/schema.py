from typing import Annotated, Any

from pydantic import BaseModel, Discriminator, Tag

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.enum.server_type import ServerType
from pycraftcore.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from pycraftcore.application_configuration.model.connector import (
    ApiConnector,
    ConnectorRegistry,
    DatabaseConnector,
    FileConnector,
    McpConnector,
    TelemetryConnector,
)
from pycraftcore.application_configuration.model.operation import (
    ApiOperation,
    FileOperation,
    McpOperation,
    OperationRegistry,
)
from pycraftcore.application_configuration.model.server import AsgiServer, ServerRegistry
from pycraftcore.logger.enum.log_level import LogLevel


def _kind_tag(value: Any) -> str:
    return value["type"] if isinstance(value, dict) else value.type.value


_ConnectorSchemaTyping = Annotated[
    Annotated[ApiConnector, Tag("api")]
    | Annotated[DatabaseConnector, Tag("database")]
    | Annotated[FileConnector, Tag("file")]
    | Annotated[TelemetryConnector, Tag("telemetry")]
    | Annotated[McpConnector, Tag("mcp")],
    Discriminator(_kind_tag),
]

_OperationSchemaTyping = Annotated[
    Annotated[ApiOperation, Tag("api")]
    | Annotated[FileOperation, Tag("file")]
    | Annotated[McpOperation, Tag("mcp")],
    Discriminator(_kind_tag),
]


class ApplicationConfigurationSchema(BaseModel):
    env: RunTypeEnvironment
    run: RunTypeApplication
    log: LogLevel
    server: dict[ServerType, dict[str, AsgiServer]]
    connector: dict[ConnectorType, dict[str, _ConnectorSchemaTyping]]
    operation: dict[str, _OperationSchemaTyping]


class MapperDomainSchema:
    @staticmethod
    def map(
        app_configuration_schema: ApplicationConfigurationSchema,
    ) -> ApplicationConfiguration:
        return ApplicationConfiguration(
            env=app_configuration_schema.env,
            run=app_configuration_schema.run,
            log=app_configuration_schema.log,
            server=ServerRegistry(app_configuration_schema.server),
            connector=ConnectorRegistry(app_configuration_schema.connector),
            operation=OperationRegistry(app_configuration_schema.operation),
        )
