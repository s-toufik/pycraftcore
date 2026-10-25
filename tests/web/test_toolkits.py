from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from pycraftcore.web.schema import ApiSettings
from tests.web.apps import EVERY_TOOLKIT
from tests.web.support import http_client, starts

pytestmark = pytest.mark.asyncio

ORDERS_API = ApiSettings(title="orders-api", version="1.4.0")


@EVERY_TOOLKIT
async def test_a_json_route_validates_its_body_and_carries_the_request_id(orders_app) -> None:
    async with http_client(orders_app(ORDERS_API)) as client:
        response = await client.post(
            "/orders", json={"reference": "A-1"}, headers={"X-Request-ID": "r9"}
        )

    assert response.status_code == 200
    assert response.json() == {"reference": "A-1 (r9)"}
    assert response.headers["x-request-id"] == "r9"


@EVERY_TOOLKIT
async def test_an_invalid_body_is_a_client_error(orders_app) -> None:
    async with http_client(orders_app(ORDERS_API)) as client:
        response = await client.post("/orders", json={"wrong": 1})

    assert 400 <= response.status_code < 500


@EVERY_TOOLKIT
async def test_a_route_answers_with_its_own_status(orders_app) -> None:
    async with http_client(orders_app(ORDERS_API)) as client:
        response = await client.get("/orders/queued")

    assert response.status_code == 202
    assert response.json() == {"reference": "queued"}


@EVERY_TOOLKIT
async def test_a_detail_handler_turns_an_exception_into_its_status(orders_app) -> None:
    async with http_client(orders_app(ORDERS_API)) as client:
        response = await client.get("/orders/unavailable")

    assert response.status_code == 503
    assert response.json() == {"detail": "no stock left"}


@EVERY_TOOLKIT
async def test_an_event_stream_sends_the_frames_untouched(orders_app) -> None:
    async with http_client(orders_app(ORDERS_API)) as client:
        response = await client.post("/orders/updates", json={"reference": "A-1"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.text == "event: placed\ndata: 1\n\nevent: shipped\ndata: A-1\n\n"


@EVERY_TOOLKIT
async def test_cors_comes_from_the_api_settings(orders_app) -> None:
    api = ApiSettings(title="orders-api", cors_origins=("*",))
    async with http_client(orders_app(api)) as client:
        response = await client.options(
            "/orders",
            headers={"Origin": "http://shop.local", "Access-Control-Request-Method": "POST"},
        )

    assert response.status_code in (200, 204)
    assert response.headers["access-control-allow-origin"] in ("*", "http://shop.local")


@EVERY_TOOLKIT
async def test_every_route_is_served_under_the_base_path_only(orders_app) -> None:
    api = ApiSettings(title="orders-api", base_path="/shop/v1")
    async with http_client(orders_app(api)) as client:
        prefixed = await client.get("/shop/v1/orders/queued")
        actuator = await client.get("/shop/v1/actuator/health")
        bare = await client.get("/orders/queued")

    assert (prefixed.status_code, actuator.status_code, bare.status_code) == (202, 200, 404)


@EVERY_TOOLKIT
async def test_no_documentation_is_served_unless_asked(orders_app) -> None:
    async with http_client(orders_app(ORDERS_API)) as client:
        statuses = [
            (await client.get(path)).status_code
            for path in ("/docs", "/docs/openapi.json", "/openapi.json", "/schema")
        ]

    assert statuses == [404, 404, 404, 404]


@EVERY_TOOLKIT
async def test_the_documentation_is_served_under_the_base_path(orders_app) -> None:
    api = ApiSettings(title="orders-api", version="1.4.0", base_path="/shop", docs=True)
    async with http_client(orders_app(api)) as client:
        ui = await client.get("/shop/docs", follow_redirects=True)
        schema = await client.get("/shop/docs/openapi.json")

    assert ui.status_code == 200
    assert ui.headers["content-type"].startswith("text/html")
    assert schema.json()["info"] == {"title": "orders-api", "version": "1.4.0"}
    assert {"/shop/orders", "/shop/orders/queued", "/shop/actuator/health"} <= set(
        schema.json()["paths"]
    )


@EVERY_TOOLKIT
async def test_the_documentation_describes_bodies_statuses_and_streams(orders_app) -> None:
    api = ApiSettings(title="orders-api", docs=True)
    async with http_client(orders_app(api)) as client:
        paths = (await client.get("/docs/openapi.json")).json()["paths"]

    order = {"$ref": "#/components/schemas/Order"}
    place_order = paths["/orders"]["post"]
    assert place_order["requestBody"]["content"]["application/json"]["schema"] == order
    assert place_order["responses"]["200"]["content"]["application/json"]["schema"] == order
    assert (
        paths["/orders/queued"]["get"]["responses"]["202"]["content"]["application/json"]["schema"]
        == order
    )
    assert "text/event-stream" in paths["/orders/updates"]["post"]["responses"]["200"]["content"]


@EVERY_TOOLKIT
@pytest.mark.parametrize("path", ["/actuator/health", "/actuator/health/liveness"])
async def test_health_and_liveness_are_always_up(orders_app, path) -> None:
    async with http_client(orders_app(ORDERS_API, ready=False)) as client:
        response = await client.get(path)

    assert (response.status_code, response.json()) == (200, {"status": "UP"})


@EVERY_TOOLKIT
@pytest.mark.parametrize(
    ("ready", "status_code", "status"), [(False, 503, "DOWN"), (True, 200, "UP")]
)
async def test_readiness_follows_the_service(orders_app, ready, status_code, status) -> None:
    async with http_client(orders_app(ORDERS_API, ready=ready)) as client:
        response = await client.get("/actuator/health/readiness")

    assert (response.status_code, response.json()) == (status_code, {"status": status})


@EVERY_TOOLKIT
async def test_info_describes_the_service(orders_app) -> None:
    async with http_client(orders_app(ORDERS_API)) as client:
        response = await client.get("/actuator/info")

    assert response.json() == {
        "name": "orders-api",
        "version": "1.2.3",
        "environment": "staging",
        "authors": "team@example.com",
    }


@EVERY_TOOLKIT
async def test_the_lifespan_wraps_the_service(orders_app) -> None:
    events: list[str] = []

    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        events.append("started")
        yield
        events.append("stopped")

    async with http_client(orders_app(ORDERS_API, lifespan=lifespan)) as client:
        await client.get("/orders/queued")

    assert events == ["started", "stopped"]


@EVERY_TOOLKIT
async def test_a_lifespan_failure_stops_the_startup_and_is_logged(orders_app, caplog) -> None:
    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        raise RuntimeError("database unreachable")
        yield

    assert await starts(orders_app(ORDERS_API, lifespan=lifespan)) is False
    assert "database unreachable" in caplog.text
