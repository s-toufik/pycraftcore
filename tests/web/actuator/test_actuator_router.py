import pytest

from pycraftcore.web.actuator import ActuatorRouter
from pycraftcore.web.enum.web_framework import WebFramework
from tests.web.support import EVERY_FRAMEWORK, build_app, http_client

pytestmark = pytest.mark.asyncio


def make_app(framework: WebFramework, ready: bool = False):
    router = ActuatorRouter(
        app_name="orders-api",
        app_version="1.2.3",
        app_deployment_environment="staging",
        app_authors="team@example.com",
        is_ready=lambda: ready,
    )
    return build_app(framework, router.routes)


@EVERY_FRAMEWORK
@pytest.mark.parametrize("path", ["/actuator/health", "/actuator/health/liveness"])
async def test_health_and_liveness_are_always_up(framework, path) -> None:
    async with http_client(make_app(framework)) as client:
        response = await client.get(path)

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


@EVERY_FRAMEWORK
async def test_readiness_is_down_until_the_app_is_ready(framework) -> None:
    async with http_client(make_app(framework)) as client:
        response = await client.get("/actuator/health/readiness")

    assert response.status_code == 503
    assert response.json() == {"status": "DOWN"}


@EVERY_FRAMEWORK
async def test_readiness_is_up_once_the_app_is_ready(framework) -> None:
    async with http_client(make_app(framework, ready=True)) as client:
        response = await client.get("/actuator/health/readiness")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


@EVERY_FRAMEWORK
async def test_info_reports_the_application(framework) -> None:
    async with http_client(make_app(framework)) as client:
        response = await client.get("/actuator/info")

    assert response.json() == {
        "name": "orders-api",
        "version": "1.2.3",
        "environment": "staging",
        "authors": "team@example.com",
    }
