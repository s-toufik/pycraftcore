from dataclasses import dataclass, field
from typing import Any

from pycraftcore.application_configuration.enum.file_operation_action import (
    FileOperationAction,
)
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model.connector import (
    ApiConnector,
    FileConnector,
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


OperationTyping = FileOperation | ApiOperation

_OPERATION_CLASS_BY_TYPE: dict[OperationType, type[OperationTyping]] = {
    OperationType.api: ApiOperation,
    OperationType.file: FileOperation,
}


@dataclass(frozen=True, slots=True)
class OperationRegistry:
    """Operations keyed by name, with per-kind typed lookups.

    Mirrors `ConnectorRegistry`: each operation declares its own `OperationType`, and a
    mismatch between that declared type and its concrete dataclass is rejected eagerly here
    instead of surfacing later as a wrong-typed lookup.
    """

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
