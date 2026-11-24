from dataclasses import dataclass, field
from typing import Any, ClassVar

from pydantic import ConfigDict

from pycraftcore.application_configuration.model.connector.database_connector import (
    DatabaseConnector,
)
from pycraftcore.application_configuration.model.operation.base_operation import BaseOperation


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
