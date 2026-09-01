from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, overload

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

_CONNECTOR_CLASS_BY_TYPE: dict[ConnectorType, type[ConnectorTyping]] = {
    ConnectorType.api: ApiConnector,
    ConnectorType.database: DatabaseConnector,
    ConnectorType.file: FileConnector,
    ConnectorType.telemetry: TelemetryConnector,
}


@dataclass(frozen=True, slots=True)
class ConnectorRegistry:
    by_type: dict[ConnectorType, dict[str, ConnectorTyping]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for kind, bucket in self.by_type.items():
            expected = _CONNECTOR_CLASS_BY_TYPE.get(kind)
            if expected is None:
                continue
            for name, connector in bucket.items():
                if not isinstance(connector, expected):
                    raise TypeError(
                        f"connector {name!r} declared under {kind.value!r} must be a "
                        f"{expected.__name__}, got {type(connector).__name__}"
                    )

    @overload
    def __getitem__(self, kind: Literal[ConnectorType.api]) -> Mapping[str, ApiConnector]: ...
    @overload
    def __getitem__(
        self, kind: Literal[ConnectorType.database]
    ) -> Mapping[str, DatabaseConnector]: ...
    @overload
    def __getitem__(self, kind: Literal[ConnectorType.file]) -> Mapping[str, FileConnector]: ...
    @overload
    def __getitem__(
        self, kind: Literal[ConnectorType.telemetry]
    ) -> Mapping[str, TelemetryConnector]: ...

    def __getitem__(self, kind: ConnectorType) -> Mapping[str, ConnectorTyping]:
        return self.by_type.get(kind, {})

    def api(self, name: str) -> ApiConnector:
        return self._get(ConnectorType.api, name, ApiConnector)

    def database(self, name: str) -> DatabaseConnector:
        return self._get(ConnectorType.database, name, DatabaseConnector)

    def file(self, name: str) -> FileConnector:
        return self._get(ConnectorType.file, name, FileConnector)

    def telemetry(self, name: str) -> TelemetryConnector:
        return self._get(ConnectorType.telemetry, name, TelemetryConnector)

    def _get[T: ConnectorTyping](self, kind: ConnectorType, name: str, expected: type[T]) -> T:
        try:
            connector = self.by_type[kind][name]
        except KeyError:
            raise KeyError(f"no {kind.value} connector named {name!r}") from None
        assert isinstance(connector, expected)
        return connector
