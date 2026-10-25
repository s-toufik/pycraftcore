from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.web.asgi import ASGIApp
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web_fastapi import (
    EventStreamResponse,
    actuator_router,
    create_app,
    detail_handler,
    event_stream,
)
from tests.web.apps.orders import Feed, OutOfStock, one_tick, orders_actuator, shipping


class Order(BaseModel):
    reference: str


def orders_app(
    api: ApiSettings,
    *,
    ready: bool = True,
    feed: Feed = one_tick,
    lifespan: Callable[[], AbstractAsyncContextManager[None]] | None = None,
    **options: Any,
) -> ASGIApp:
    router = APIRouter(tags=["orders"])

    @router.post("/orders")
    async def place(order: Order) -> Order:
        return Order(reference=f"{order.reference} ({request_id_context.get()})")

    @router.get("/orders/queued", status_code=202)
    async def queued() -> Order:
        return Order(reference="queued")

    @router.get("/orders/unavailable")
    async def unavailable() -> Order:
        raise OutOfStock("no stock left")

    @router.post("/orders/updates", response_class=EventStreamResponse)
    async def updates(order: Order) -> EventStreamResponse:
        return event_stream(shipping(order.reference))

    @router.get("/feed", response_class=EventStreamResponse)
    async def follow() -> EventStreamResponse:
        return event_stream(feed())

    return create_app(
        api,
        routes=[router, actuator_router(orders_actuator(ready))],
        lifespan=lifespan,
        exception_handlers={OutOfStock: detail_handler(503)},
        **options,
    )
