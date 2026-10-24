from collections.abc import Awaitable, Callable

from pycraftcore.web.actuator.enum.health_status import HealthStatus
from pycraftcore.web.actuator.schema.actuator_response import HealthSchema, InfoSchema
from pycraftcore.web.schema.http_route import HttpResult, HttpRoute

TAGS: tuple[str, ...] = ("actuator",)


class ActuatorRouter:
    PREFIX = "/actuator"

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_deployment_environment: str,
        app_authors: str,
        is_ready: Callable[[], bool],
    ) -> None:
        self._info_schema = InfoSchema(
            name=app_name,
            version=app_version,
            environment=app_deployment_environment,
            authors=app_authors,
        )
        self._is_ready = is_ready

    @property
    def routes(self) -> list[HttpRoute]:
        return [
            self._route("/health", self._health, HealthSchema),
            self._route("/health/liveness", self._health, HealthSchema),
            self._route("/health/readiness", self._readiness, HealthSchema),
            self._route("/info", self._info, InfoSchema),
        ]

    def _route(
        self,
        path: str,
        handler: Callable[[], Awaitable[HealthSchema | InfoSchema | HttpResult]],
        response: type[HealthSchema | InfoSchema],
    ) -> HttpRoute:
        return HttpRoute("GET", f"{self.PREFIX}{path}", handler, response=response, tags=TAGS)

    @staticmethod
    async def _health() -> HealthSchema:
        return HealthSchema(status=HealthStatus.UP)

    async def _readiness(self) -> HealthSchema | HttpResult:
        if self._is_ready():
            return HealthSchema(status=HealthStatus.UP)
        return HttpResult(HealthSchema(status=HealthStatus.DOWN), status_code=503)

    async def _info(self) -> InfoSchema:
        return self._info_schema
