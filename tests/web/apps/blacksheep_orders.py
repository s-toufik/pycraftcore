from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from blacksheep import Request, Response, Router, json
from blacksheep.server.openapi.common import ContentInfo, ResponseInfo
from pydantic import BaseModel

from pycraftcore.context.request_id_context import request_id_context
from pycraftcore.web.asgi import ASGIApp
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web.sse import EVENT_STREAM_MEDIA_TYPE
from pycraftcore.web_blacksheep import (
    actuator_router,
    create_app,
    detail_handler,
    event_stream,
    openapi_handler,
)
from tests.web.apps.orders import Feed, OutOfStock, one_tick, orders_actuator, shipping

EVENT_STREAM = ResponseInfo(
    "Event stream", content=[ContentInfo(str, content_type=EVENT_STREAM_MEDIA_TYPE)]
)


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
    router = Router()
    docs = openapi_handler(api)

    @docs(tags=["orders"])
    @router.post("/orders")
    async def place(order: Order) -> Order:
        return Order(reference=f"{order.reference} ({request_id_context.get()})")

    @docs(tags=["orders"], responses={202: ResponseInfo("Queued", content=[ContentInfo(Order)])})
    @router.get("/orders/queued")
    async def queued() -> Response:
        return json(Order(reference="queued").model_dump(), status=202)

    @docs(tags=["orders"])
    @router.get("/orders/unavailable")
    async def unavailable() -> Order:
        raise OutOfStock("no stock left")

    @docs(tags=["orders"], responses={200: EVENT_STREAM})
    @router.post("/orders/updates")
    async def updates(request: Request, order: Order) -> Response:
        return event_stream(shipping(order.reference), request)

    @docs(responses={200: EVENT_STREAM})
    @router.get("/feed")
    async def follow(request: Request) -> Response:
        return event_stream(feed(), request)

    return create_app(
        api,
        routes=[router, actuator_router(orders_actuator(ready))],
        lifespan=lifespan,
        exception_handlers={OutOfStock: detail_handler(503)},
        openapi=docs,
        **options,
    )
