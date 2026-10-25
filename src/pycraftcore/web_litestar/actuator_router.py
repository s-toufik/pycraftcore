from litestar import Response, Router, get

from pycraftcore.web.actuator import ACTUATOR_PATH, ACTUATOR_TAG, Actuator, HealthSchema, InfoSchema


def actuator_router(actuator: Actuator) -> Router:
    @get("/health")
    async def health() -> HealthSchema:
        return actuator.health()

    @get("/health/liveness")
    async def liveness() -> HealthSchema:
        return actuator.health()

    @get("/health/readiness")
    async def readiness() -> Response[HealthSchema]:
        report = actuator.readiness()
        return Response(report, status_code=report.status_code)

    @get("/info")
    async def info() -> InfoSchema:
        return actuator.info()

    return Router(
        path=ACTUATOR_PATH,
        route_handlers=[health, liveness, readiness, info],
        tags=[ACTUATOR_TAG],
    )
