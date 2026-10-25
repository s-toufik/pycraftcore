from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

import msgspec
from litestar import get, post
from litestar.params import JSONBody
from litestar.response import Stream

from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.web.asgi import ASGIApp
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web.sse import EVENT_STREAM_MEDIA_TYPE
from pycraftcore.web_litestar import actuator_router, create_app, detail_handler, event_stream
from tests.web.apps.orders import Feed, OutOfStock, one_tick, orders_actuator, shipping


class Order(msgspec.Struct):
    reference: str


def orders_app(
    api: ApiSettings,
    *,
    ready: bool = True,
    feed: Feed = one_tick,
    lifespan: Callable[[], AbstractAsyncContextManager[None]] | None = None,
    **options: Any,
) -> ASGIApp:
    @post("/orders", status_code=200, tags=["orders"])
    async def place(data: JSONBody[Order]) -> Order:
        return Order(reference=f"{data.reference} ({request_id_context.get()})")

    @get("/orders/queued", status_code=202, tags=["orders"])
    async def queued() -> Order:
        return Order(reference="queued")

    @get("/orders/unavailable", tags=["orders"])
    async def unavailable() -> Order:
        raise OutOfStock("no stock left")

    @post("/orders/updates", status_code=200, media_type=EVENT_STREAM_MEDIA_TYPE, tags=["orders"])
    async def updates(data: JSONBody[Order]) -> Stream:
        return event_stream(shipping(data.reference))

    @get("/feed", media_type=EVENT_STREAM_MEDIA_TYPE)
    async def follow() -> Stream:
        return event_stream(feed())

    return create_app(
        api,
        routes=[
            place,
            queued,
            unavailable,
            updates,
            follow,
            actuator_router(orders_actuator(ready)),
        ],
        lifespan=lifespan,
        exception_handlers={OutOfStock: detail_handler(503)},
        **options,
    )
