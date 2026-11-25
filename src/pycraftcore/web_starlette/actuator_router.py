from dataclasses import asdict

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from pycraftcore.web.actuator import ACTUATOR_PATH, Actuator, HealthSchema


def actuator_router(actuator: Actuator) -> Mount:
    async def health(_request: Request) -> JSONResponse:
        return _report(actuator.health())

    async def readiness(_request: Request) -> JSONResponse:
        return _report(actuator.readiness())

    async def info(_request: Request) -> JSONResponse:
        return JSONResponse(asdict(actuator.info()))

    return Mount(
        ACTUATOR_PATH,
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/health/liveness", health, methods=["GET"]),
            Route("/health/readiness", readiness, methods=["GET"]),
            Route("/info", info, methods=["GET"]),
        ],
    )


def _report(report: HealthSchema) -> JSONResponse:
    return JSONResponse(report.as_dict(), status_code=report.status_code)
