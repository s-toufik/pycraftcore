from dataclasses import dataclass, field

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.authentication import AuthTyping


@dataclass(slots=True)
class BaseConnector:
    name: str
    type: ConnectorType
    auth: AuthTyping


@dataclass(slots=True)
class ApiConnector(BaseConnector):
    base_url: str
    timeout: int
    retry: int
    certificate: str | None = field(default=None)


@dataclass(slots=True)
class DatabaseConnector(BaseConnector):
    engine: str
    host: str
    port: int
    default_name: str
    pool: dict[str, int]


@dataclass(slots=True)
class FileConnector(BaseConnector):
    base_path: str


@dataclass(slots=True)
class TelemetryConnector(BaseConnector):
    host: str
    port: int


ConnectorTyping = ApiConnector | FileConnector | DatabaseConnector | TelemetryConnector
