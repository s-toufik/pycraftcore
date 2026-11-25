from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Final

from pycraftcore.web.actuator.enum.health_status import HealthStatus
from pycraftcore.web.actuator.schema.actuator_response import (
    DependencyReport,
    HealthSchema,
    InfoSchema,
)

ACTUATOR_PATH: Final[str] = "/actuator"
ACTUATOR_TAG: Final[str] = "actuator"


@dataclass(frozen=True, slots=True)
class Actuator:
    name: str
    version: str
    environment: str
    authors: str
    is_ready: Callable[[], bool]
    dependencies: Callable[[], Mapping[str, DependencyReport]] = field(default=dict)

    def health(self) -> HealthSchema:
        return HealthSchema(status=HealthStatus.UP, dependencies=dict(self.dependencies()) or None)

    def readiness(self) -> HealthSchema:
        return HealthSchema(status=HealthStatus.UP if self.is_ready() else HealthStatus.DOWN)

    def info(self) -> InfoSchema:
        return InfoSchema(
            name=self.name, version=self.version, environment=self.environment, authors=self.authors
        )
