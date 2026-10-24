from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from pydantic import BaseModel

from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.http.middleware import RequestIDMiddleware
from pycraftcore.web.frameworks import web_application_factory
from pycraftcore.web.schema.http_route import HttpResult, HttpRoute, ResponseKind
from pycraftcore.web.schema.web_application import WebApplication
from tests.web.support import EVERY_FRAMEWORK, build_app, http_client, starts

pytestmark = pytest.mark.asyncio


class Order(BaseModel):
    reference: str


class OutOfStock(Exception): ...


async def place(order: Order) -> Order:
    return Order(reference=f"{order.reference} ({request_id_context.get()})")


async def accepted() -> HttpResult:
    return HttpResult(Order(reference="queued"), status_code=202)


async def unavailable() -> Order:
    raise OutOfStock("no stock left")


async def updates(order: Order) -> AsyncIterator[bytes]:
    async def stream() -> AsyncIterator[bytes]:
        yield b"event: placed\ndata: 1\n\n"
        yield f"event: shipped\ndata: {order.reference}\n\n".encode()

    return stream()


ROUTES = [
    HttpRoute("POST", "/orders", place, body=Order, response=Order),
    HttpRoute("GET", "/orders/queued", accepted, response=Order, status_code=202),
    HttpRoute("GET", "/orders/unavailable", unavailable, response=Order),
    HttpRoute("POST", "/orders/updates", updates, body=Order, kind=ResponseKind.EVENT_STREAM),
]


def app_for(framework):
    return build_app(
        framework,
        ROUTES,
        errors={OutOfStock: 503},
        middleware=(RequestIDMiddleware,),
        cors_origins=("*",),
    )


@EVERY_FRAMEWORK
async def test_a_json_route_validates_its_body_and_answers_200(framework) -> None:
    async with http_client(app_for(framework)) as client:
        response = await client.post(
            "/orders", json={"reference": "A-1"}, headers={"X-Request-ID": "r9"}
        )

    assert response.status_code == 200
    assert response.json() == {"reference": "A-1 (r9)"}
    assert response.headers["x-request-id"] == "r9"


@EVERY_FRAMEWORK
async def test_an_invalid_body_is_a_client_error(framework) -> None:
    async with http_client(app_for(framework)) as client:
        response = await client.post("/orders", json={"wrong": 1})

    assert 400 <= response.status_code < 500


@EVERY_FRAMEWORK
async def test_an_http_result_sets_its_own_status(framework) -> None:
    async with http_client(app_for(framework)) as client:
        response = await client.get("/orders/queued")

    assert response.status_code == 202
    assert response.json() == {"reference": "queued"}


@EVERY_FRAMEWORK
async def test_a_mapped_exception_becomes_its_status_with_a_detail(framework) -> None:
    async with http_client(app_for(framework)) as client:
        response = await client.get("/orders/unavailable")

    assert response.status_code == 503
    assert response.json() == {"detail": "no stock left"}


@EVERY_FRAMEWORK
async def test_an_event_stream_route_streams_the_frames_untouched(framework) -> None:
    async with http_client(app_for(framework)) as client:
        response = await client.post("/orders/updates", json={"reference": "A-1"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.text == "event: placed\ndata: 1\n\nevent: shipped\ndata: A-1\n\n"


@EVERY_FRAMEWORK
async def test_cors_preflight_is_allowed(framework) -> None:
    async with http_client(app_for(framework)) as client:
        response = await client.options(
            "/orders",
            headers={"Origin": "http://shop.local", "Access-Control-Request-Method": "POST"},
        )

    assert response.status_code in (200, 204)
    assert response.headers["access-control-allow-origin"] in ("*", "http://shop.local")


@EVERY_FRAMEWORK
async def test_routes_are_served_under_the_base_path_only(framework) -> None:
    async with http_client(build_app(framework, ROUTES, base_path="/shop/v1")) as client:
        prefixed = await client.get("/shop/v1/orders/queued")
        bare = await client.get("/orders/queued")

    assert prefixed.status_code == 202
    assert bare.status_code == 404


@EVERY_FRAMEWORK
async def test_no_documentation_is_served_unless_asked(framework) -> None:
    async with http_client(app_for(framework)) as client:
        ui = await client.get("/docs")
        schema = await client.get("/docs/openapi.json")
        fastapi_default = await client.get("/openapi.json")

    assert (ui.status_code, schema.status_code, fastapi_default.status_code) == (404, 404, 404)


@EVERY_FRAMEWORK
async def test_the_documentation_is_served_under_the_base_path(framework) -> None:
    app = build_app(framework, ROUTES, base_path="/shop/v1", docs=True)
    async with http_client(app) as client:
        ui = await client.get("/shop/v1/docs")
        schema = await client.get("/shop/v1/docs/openapi.json")

    assert ui.status_code == 200
    assert ui.headers["content-type"].startswith("text/html")
    assert schema.status_code == 200
    assert schema.json()["info"]["title"] == "orders-api"
    assert set(schema.json()["paths"]) == {
        "/shop/v1/orders",
        "/shop/v1/orders/queued",
        "/shop/v1/orders/unavailable",
        "/shop/v1/orders/updates",
    }


@EVERY_FRAMEWORK
async def test_the_documentation_describes_bodies_responses_and_streams(framework) -> None:
    async with http_client(build_app(framework, ROUTES, docs=True)) as client:
        paths = (await client.get("/docs/openapi.json")).json()["paths"]

    place_order = paths["/orders"]["post"]
    queued = paths["/orders/queued"]["get"]
    updates = paths["/orders/updates"]["post"]
    order = {"$ref": "#/components/schemas/Order"}
    assert place_order["requestBody"]["content"]["application/json"]["schema"] == order
    assert place_order["responses"]["200"]["content"]["application/json"]["schema"] == order
    assert queued["responses"]["202"]["content"]["application/json"]["schema"] == order
    assert list(updates["responses"]["200"]["content"]) == ["text/event-stream"]


@EVERY_FRAMEWORK
async def test_routes_are_read_once_the_lifespan_started(framework) -> None:
    booted: list[HttpRoute] = []

    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        booted.append(HttpRoute("GET", "/orders/queued", accepted, response=Order))
        yield

    app = web_application_factory(framework).create(
        WebApplication(title="orders-api", lifespan=lifespan, routes=lambda: booted)
    )
    async with http_client(app) as client:
        response = await client.get("/orders/queued")

    assert response.status_code == 202


@EVERY_FRAMEWORK
async def test_a_lifespan_failure_stops_the_startup_and_is_logged(framework, caplog) -> None:
    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        raise RuntimeError("database unreachable")
        yield

    assert await starts(build_app(framework, ROUTES, lifespan=lifespan)) is False
    assert "database unreachable" in caplog.text
