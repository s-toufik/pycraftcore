from fastapi import APIRouter, Response

from pycraftcore.web.actuator import ACTUATOR_PATH, ACTUATOR_TAG, Actuator, HealthSchema, InfoSchema


def actuator_router(actuator: Actuator) -> APIRouter:
    router = APIRouter(prefix=ACTUATOR_PATH, tags=[ACTUATOR_TAG])

    @router.get("/health")
    async def health() -> HealthSchema:
        return actuator.health()

    @router.get("/health/liveness")
    async def liveness() -> HealthSchema:
        return actuator.health()

    @router.get("/health/readiness", responses={503: {"model": HealthSchema}})
    async def readiness(response: Response) -> HealthSchema:
        report = actuator.readiness()
        response.status_code = report.status_code
        return report

    @router.get("/info")
    async def info() -> InfoSchema:
        return actuator.info()

    return router
