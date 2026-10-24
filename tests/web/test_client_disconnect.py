import asyncio
from collections.abc import AsyncIterator

import httpx
import pytest

from pycraftcore.web.schema.http_route import HttpRoute, ResponseKind
from tests.web.support import EVERY_FRAMEWORK, build_app, running_server

pytestmark = pytest.mark.asyncio


class SilentFeed:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.closed = asyncio.Event()

    async def open(self) -> AsyncIterator[bytes]:
        return self._frames()

    async def _frames(self) -> AsyncIterator[bytes]:
        self.started.set()
        try:
            yield b"event: opened\ndata: 1\n\n"
            await asyncio.sleep(30)
            yield b"event: never\ndata: 2\n\n"
        finally:
            self.closed.set()


@EVERY_FRAMEWORK
async def test_a_client_leaving_closes_the_stream_it_was_reading(framework) -> None:
    feed = SilentFeed()
    app = build_app(
        framework, [HttpRoute("GET", "/feed", feed.open, kind=ResponseKind.EVENT_STREAM)]
    )

    async with running_server(app) as base_url:
        async with httpx.AsyncClient(base_url=base_url) as client:
            async with client.stream("GET", "/feed") as response:
                assert response.status_code == 200
                await feed.started.wait()

        await asyncio.wait_for(feed.closed.wait(), timeout=5)
