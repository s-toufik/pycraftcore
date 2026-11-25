from typing import Any

from litestar import Response, Router, get

from pycraftcore.web.actuator import ACTUATOR_PATH, ACTUATOR_TAG, Actuator, HealthSchema, InfoSchema


def actuator_router(actuator: Actuator) -> Router:
    @get("/health")
    async def health() -> Response[dict[str, Any]]:
        return _report(actuator.health())

    @get("/health/liveness")
    async def liveness() -> Response[dict[str, Any]]:
        return _report(actuator.health())

    @get("/health/readiness")
    async def readiness() -> Response[dict[str, Any]]:
        return _report(actuator.readiness())

    @get("/info")
    async def info() -> InfoSchema:
        return actuator.info()

    return Router(
        path=ACTUATOR_PATH,
        route_handlers=[health, liveness, readiness, info],
        tags=[ACTUATOR_TAG],
    )


def _report(report: HealthSchema) -> Response[dict[str, Any]]:
    return Response(report.as_dict(), status_code=report.status_code)
