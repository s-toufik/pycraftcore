from dataclasses import dataclass, field
from typing import ClassVar

from pydantic import ConfigDict

from pycraftcore.application_configuration.model.connector.base_connector import BaseConnector


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
