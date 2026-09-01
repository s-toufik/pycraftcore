from typing import Annotated, Any

from pydantic import BaseModel, Discriminator, Tag

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
    ApiConnector,
    ConnectorRegistry,
    DatabaseConnector,
    FileConnector,
    TelemetryConnector,
)
from pycraftcore.application_configuration.model.operation import (
    ApiOperation,
    FileOperation,
    OperationRegistry,
)


def _kind_tag(value: Any) -> str:
    """Discriminator: read `type` off a raw dict (pre-coercion) or an already-built dataclass."""
    return value["type"] if isinstance(value, dict) else value.type.value


_ConnectorSchemaTyping = Annotated[
    Annotated[ApiConnector, Tag("api")]
    | Annotated[DatabaseConnector, Tag("database")]
    | Annotated[FileConnector, Tag("file")]
    | Annotated[TelemetryConnector, Tag("telemetry")],
    Discriminator(_kind_tag),
]

_OperationSchemaTyping = Annotated[
    Annotated[ApiOperation, Tag("api")] | Annotated[FileOperation, Tag("file")],
    Discriminator(_kind_tag),
]


class ApplicationConfigurationSchema(BaseModel):
    env: RunTypeEnvironment
    run: RunTypeApplication
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
            connector=ConnectorRegistry(app_configuration_schema.connector),
            operation=OperationRegistry(app_configuration_schema.operation),
        )
