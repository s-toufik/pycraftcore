import asyncio
from collections.abc import AsyncIterator

import httpx
import pytest

from pycraftcore.web.schema import ApiSettings
from tests.web.apps import EVERY_TOOLKIT
from tests.web.support import running_server

pytestmark = pytest.mark.asyncio


class SilentFeed:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.closed = asyncio.Event()

    async def frames(self) -> AsyncIterator[bytes]:
        self.started.set()
        try:
            yield b"event: opened\ndata: 1\n\n"
            await asyncio.sleep(30)
            yield b"event: never\ndata: 2\n\n"
        finally:
            self.closed.set()


class BusyFeed(SilentFeed):
    async def frames(self) -> AsyncIterator[bytes]:
        self.started.set()
        try:
            for index in range(100_000):
                yield f"event: tick\ndata: {index}\n\n".encode()
                await asyncio.sleep(0.001)
        finally:
            self.closed.set()


@EVERY_TOOLKIT
async def test_a_client_leaving_closes_the_stream_it_was_reading(orders_app) -> None:
    feed = SilentFeed()
    app = orders_app(ApiSettings(title="orders-api"), feed=feed.frames)

    async with running_server(app) as base_url:
        async with httpx.AsyncClient(base_url=base_url) as client:
            async with client.stream("GET", "/feed") as response:
                assert response.status_code == 200
                await feed.started.wait()

        await asyncio.wait_for(feed.closed.wait(), timeout=5)


@EVERY_TOOLKIT
async def test_a_client_leaving_a_busy_stream_closes_it(orders_app) -> None:
    feed = BusyFeed()
    app = orders_app(ApiSettings(title="orders-api"), feed=feed.frames)

    async with running_server(app) as base_url:
        async with httpx.AsyncClient(base_url=base_url) as client:
            async with client.stream("GET", "/feed") as response:
                assert response.status_code == 200
                await anext(response.aiter_bytes())

        await asyncio.wait_for(feed.closed.wait(), timeout=5)
