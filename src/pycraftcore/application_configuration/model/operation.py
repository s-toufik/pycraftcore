from dataclasses import dataclass, field
from typing import Any, ClassVar

from pydantic import ConfigDict

from pycraftcore.application_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model.connector import (
    A2aConnector,
    ApiConnector,
    DatabaseConnector,
    FileConnector,
    McpConnector,
)
from pycraftcore.http.enum.http_method import HttpMethod


@dataclass(slots=True)
class BaseOperation:
    name: str
    type: OperationType


@dataclass(slots=True)
class ApiOperation(BaseOperation):
    connector: ApiConnector
    endpoint: str
    method: HttpMethod
    parameters: dict[str, Any]


@dataclass(slots=True)
class FileOperation(BaseOperation):
    connector: FileConnector
    action: FileOperationAction
    parameters: dict[str, Any]


@dataclass(slots=True)
class McpOperation(BaseOperation):
    connector: McpConnector
    parameters: dict[str, Any]


@dataclass(slots=True)
class A2aOperation(BaseOperation):
    connector: A2aConnector
    parameters: dict[str, Any]


@dataclass(slots=True)
class DatabaseOperation(BaseOperation):
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    connector: DatabaseConnector
    database: str
    collections: dict[str, str] = field(default_factory=dict)
    ttl: int | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.database.strip():
            raise ValueError(f"database operation {self.name!r} needs a database")
        if self.ttl is not None and self.ttl < 0:
            raise ValueError(f"database operation {self.name!r}: ttl must be 0 or more")

    def collection(self, role: str) -> str:
        try:
            return self.collections[role]
        except KeyError:
            raise KeyError(f"database operation {self.name!r} has no collection {role!r}") from None


OperationTyping = FileOperation | ApiOperation | McpOperation | A2aOperation | DatabaseOperation

_OPERATION_CLASS_BY_TYPE: dict[OperationType, type[OperationTyping]] = {
    OperationType.api: ApiOperation,
    OperationType.file: FileOperation,
    OperationType.mcp: McpOperation,
    OperationType.a2a: A2aOperation,
    OperationType.database: DatabaseOperation,
}


@dataclass(frozen=True, slots=True)
class OperationRegistry:
    by_name: dict[str, OperationTyping] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, operation in self.by_name.items():
            expected = _OPERATION_CLASS_BY_TYPE.get(operation.type)
            if expected is None:
                continue
            if not isinstance(operation, expected):
                raise TypeError(
                    f"operation {name!r} declared type {operation.type.value!r} but is a "
                    f"{type(operation).__name__}, expected {expected.__name__}"
                )

    def api(self, name: str) -> ApiOperation:
        return self._get(name, ApiOperation)

    def file(self, name: str) -> FileOperation:
        return self._get(name, FileOperation)

    def mcp(self, name: str) -> McpOperation:
        return self._get(name, McpOperation)

    def a2a(self, name: str) -> A2aOperation:
        return self._get(name, A2aOperation)

    def database(self, name: str) -> DatabaseOperation:
        return self._get(name, DatabaseOperation)

    def _get[T: OperationTyping](self, name: str, expected: type[T]) -> T:
        try:
            operation = self.by_name[name]
        except KeyError:
            raise KeyError(f"no operation named {name!r}") from None
        if not isinstance(operation, expected):
            raise TypeError(
                f"operation {name!r} is a {type(operation).__name__}, not {expected.__name__}"
            )
        return operation
