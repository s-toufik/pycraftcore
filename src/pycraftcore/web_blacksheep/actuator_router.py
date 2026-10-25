from dataclasses import asdict

from blacksheep import Response, Router, json

from pycraftcore.web.actuator import ACTUATOR_PATH, Actuator, HealthSchema, InfoSchema


def actuator_router(actuator: Actuator) -> Router:
    router = Router(prefix=ACTUATOR_PATH)

    @router.get("/health")
    async def health() -> HealthSchema:
        return actuator.health()

    @router.get("/health/liveness")
    async def liveness() -> HealthSchema:
        return actuator.health()

    @router.get("/health/readiness")
    async def readiness() -> Response:
        report = actuator.readiness()
        return json(asdict(report), status=report.status_code)

    @router.get("/info")
    async def info() -> InfoSchema:
        return actuator.info()

    return router
