from dataclasses import dataclass, field

from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model.operation.a2a_operation import A2aOperation
from pycraftcore.application_configuration.model.operation.api_operation import ApiOperation
from pycraftcore.application_configuration.model.operation.database_operation import (
    DatabaseOperation,
)
from pycraftcore.application_configuration.model.operation.file_operation import FileOperation
from pycraftcore.application_configuration.model.operation.mcp_operation import McpOperation

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
