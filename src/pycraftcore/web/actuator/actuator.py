from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from pycraftcore.web.actuator.enum.health_status import HealthStatus
from pycraftcore.web.actuator.schema.actuator_response import HealthSchema, InfoSchema

ACTUATOR_PATH: Final[str] = "/actuator"
ACTUATOR_TAG: Final[str] = "actuator"


@dataclass(frozen=True, slots=True)
class Actuator:
    name: str
    version: str
    environment: str
    authors: str
    is_ready: Callable[[], bool]

    def health(self) -> HealthSchema:
        return HealthSchema(status=HealthStatus.UP)

    def readiness(self) -> HealthSchema:
        return HealthSchema(status=HealthStatus.UP if self.is_ready() else HealthStatus.DOWN)

    def info(self) -> InfoSchema:
        return InfoSchema(
            name=self.name, version=self.version, environment=self.environment, authors=self.authors
        )
