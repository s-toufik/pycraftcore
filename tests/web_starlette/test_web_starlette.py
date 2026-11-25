from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from pycraftcore.web.actuator import Actuator, DependencyReport, HealthStatus
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web_starlette import actuator_router, create_app


async def hello(_request) -> PlainTextResponse:
    return PlainTextResponse("hello")


def actuator(ready: bool = True, dependencies=dict) -> Actuator:
    return Actuator("toolbox", "1.3.0", "homelab", "team@example.com", lambda: ready, dependencies)


def test_routes_carry_the_request_id_and_sit_under_the_base_path() -> None:
    app = create_app(ApiSettings(title="t", base_path="/api"), routes=[Route("/hello", hello)])

    with TestClient(app) as client:
        response = client.get("/api/hello", headers={"X-Request-ID": "r1"})
        outside = client.get("/hello")

    assert (response.text, response.headers["x-request-id"]) == ("hello", "r1")
    assert outside.status_code == 404


def test_cors_origins_are_allowed_and_the_lifespan_runs() -> None:
    events: list[str] = []

    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        events.append("up")
        yield
        events.append("down")

    app = create_app(
        ApiSettings(title="t", cors_origins=("https://ui.example.com",)),
        routes=[Route("/hello", hello)],
        lifespan=lifespan,
    )

    with TestClient(app) as client:
        response = client.get("/hello", headers={"Origin": "https://ui.example.com"})

    assert response.headers["access-control-allow-origin"] == "https://ui.example.com"
    assert events == ["up", "down"]


def test_the_actuator_answers_health_readiness_and_info() -> None:
    app = create_app(ApiSettings(title="t"), routes=[actuator_router(actuator(ready=False))])

    with TestClient(app) as client:
        health = client.get("/actuator/health")
        liveness = client.get("/actuator/health/liveness")
        readiness = client.get("/actuator/health/readiness")
        info = client.get("/actuator/info")

    assert (health.status_code, health.json()) == (200, {"status": "UP"})
    assert liveness.json() == {"status": "UP"}
    assert (readiness.status_code, readiness.json()) == (503, {"status": "DOWN"})
    assert info.json() == {
        "name": "toolbox",
        "version": "1.3.0",
        "environment": "homelab",
        "authors": "team@example.com",
    }


def test_health_lists_the_dependencies_when_there_are_some() -> None:
    reports = {
        "grafana": DependencyReport(HealthStatus.UP, "2026-11-25T10:00:00+00:00"),
        "mongodb": DependencyReport(HealthStatus.DOWN, "2026-11-25T10:01:00+00:00", "refused"),
    }
    app = create_app(
        ApiSettings(title="t"), routes=[actuator_router(actuator(dependencies=lambda: reports))]
    )

    with TestClient(app) as client:
        health = client.get("/actuator/health").json()

    assert health == {
        "status": "UP",
        "dependencies": {
            "grafana": {"status": "UP", "since": "2026-11-25T10:00:00+00:00"},
            "mongodb": {"status": "DOWN", "since": "2026-11-25T10:01:00+00:00", "error": "refused"},
        },
    }
