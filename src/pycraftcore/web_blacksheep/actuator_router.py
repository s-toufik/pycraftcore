from blacksheep import Response, Router, json

from pycraftcore.web.actuator import ACTUATOR_PATH, Actuator, HealthSchema, InfoSchema


def actuator_router(actuator: Actuator) -> Router:
    router = Router(prefix=ACTUATOR_PATH)

    @router.get("/health")
    async def health() -> Response:
        return _report(actuator.health())

    @router.get("/health/liveness")
    async def liveness() -> Response:
        return _report(actuator.health())

    @router.get("/health/readiness")
    async def readiness() -> Response:
        return _report(actuator.readiness())

    @router.get("/info")
    async def info() -> InfoSchema:
        return actuator.info()

    return router


def _report(report: HealthSchema) -> Response:
    return json(report.as_dict(), status=report.status_code)
