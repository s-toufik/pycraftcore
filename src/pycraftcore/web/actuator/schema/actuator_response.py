from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pycraftcore.web.actuator.enum.health_status import HealthStatus


@dataclass(frozen=True, slots=True)
class DependencyReport:
    status: HealthStatus
    since: str
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        report: dict[str, Any] = {"status": self.status, "since": self.since}
        if self.error is not None:
            report["error"] = self.error
        return report


@dataclass(frozen=True, slots=True)
class HealthSchema:
    status: HealthStatus
    dependencies: Mapping[str, DependencyReport] | None = None

    @property
    def status_code(self) -> int:
        return 200 if self.status is HealthStatus.UP else 503

    def as_dict(self) -> dict[str, Any]:
        report: dict[str, Any] = {"status": self.status}
        if self.dependencies:
            report["dependencies"] = {
                name: dependency.as_dict() for name, dependency in self.dependencies.items()
            }
        return report


@dataclass(frozen=True, slots=True)
class InfoSchema:
    name: str
    version: str
    environment: str
    authors: str
