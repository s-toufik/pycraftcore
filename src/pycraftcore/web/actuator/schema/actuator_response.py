from dataclasses import dataclass

from pycraftcore.web.actuator.enum.health_status import HealthStatus


@dataclass(frozen=True, slots=True)
class HealthSchema:
    status: HealthStatus

    @property
    def status_code(self) -> int:
        return 200 if self.status is HealthStatus.UP else 503


@dataclass(frozen=True, slots=True)
class InfoSchema:
    name: str
    version: str
    environment: str
    authors: str
