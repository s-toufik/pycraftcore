from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar, Literal, overload

from pydantic import ConfigDict

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


@dataclass(frozen=True, slots=True)
class DatabasePool:
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    min: int = 1
    max: int = 1

    def __post_init__(self) -> None:
        if self.min < 0:
            raise ValueError("pool min must be 0 or more")
        if self.max < 1:
            raise ValueError("pool max must be 1 or more")
        if self.max < self.min:
            raise ValueError("pool max must be greater than or equal to min")


@dataclass(slots=True)
class DatabaseConnector(BaseConnector):
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    engine: str
    host: str
    port: int
    timeout: int = 5
    pool: DatabasePool = field(default_factory=DatabasePool)

    def __post_init__(self) -> None:
        if self.timeout <= 0:
            raise ValueError("database timeout must be greater than 0")


@dataclass(slots=True)
class FileConnector(BaseConnector):
    base_path: str


@dataclass(slots=True)
class TelemetryConnector(BaseConnector):
    host: str | None
    port: int | None


@dataclass(frozen=True, slots=True)
class McpRefresh:
    interval: float = 60.0
    retry_delay: float = 5.0
    max_retry_delay: float = 60.0

    def __post_init__(self) -> None:
        if self.interval <= 0:
            raise ValueError("refresh interval must be greater than 0")
        if self.retry_delay <= 0:
            raise ValueError("refresh retry_delay must be greater than 0")
        if self.max_retry_delay < self.retry_delay:
            raise ValueError("refresh max_retry_delay must be greater than or equal to retry_delay")


@dataclass(slots=True)
class McpConnector(BaseConnector):
    base_url: str
    timeout: int
    transport: Literal["sse", "streamable_http"] = "streamable_http"
    certificate: str | None = field(default=None)
    refresh: McpRefresh = field(default_factory=McpRefresh)


@dataclass(slots=True)
class A2aConnector(BaseConnector):
    base_url: str
    timeout: int
    binding: Literal["JSONRPC", "HTTP+JSON", "GRPC"] = "JSONRPC"
    certificate: str | None = field(default=None)


ConnectorTyping = (
    ApiConnector
    | FileConnector
    | DatabaseConnector
    | TelemetryConnector
    | McpConnector
    | A2aConnector
)

_CONNECTOR_CLASS_BY_TYPE: dict[ConnectorType, type[ConnectorTyping]] = {
    ConnectorType.api: ApiConnector,
    ConnectorType.database: DatabaseConnector,
    ConnectorType.file: FileConnector,
    ConnectorType.telemetry: TelemetryConnector,
    ConnectorType.mcp: McpConnector,
    ConnectorType.a2a: A2aConnector,
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
    @overload
    def __getitem__(self, kind: Literal[ConnectorType.mcp]) -> Mapping[str, McpConnector]: ...
    @overload
    def __getitem__(self, kind: Literal[ConnectorType.a2a]) -> Mapping[str, A2aConnector]: ...

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

    def mcp(self, name: str) -> McpConnector:
        return self._get(ConnectorType.mcp, name, McpConnector)

    def a2a(self, name: str) -> A2aConnector:
        return self._get(ConnectorType.a2a, name, A2aConnector)

    def _get[T: ConnectorTyping](self, kind: ConnectorType, name: str, expected: type[T]) -> T:
        try:
            connector = self.by_type[kind][name]
        except KeyError:
            raise KeyError(f"no {kind.value} connector named {name!r}") from None
        assert isinstance(connector, expected)
        return connector
