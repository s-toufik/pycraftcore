import asyncio
from collections.abc import AsyncIterator
from contextlib import aclosing

import pytest

from pycraftcore.web.sse import SSE_HEARTBEAT, with_heartbeat
from pycraftcore.web.streaming import IDLE, cancel_on_disconnect, with_idle_ticks

pytestmark = pytest.mark.asyncio


class Source:
    def __init__(self, *items: str, pause: float = 0.0, then_raise: Exception | None = None):
        self._items = items
        self._pause = pause
        self._then_raise = then_raise
        self.closed = False

    async def __call__(self) -> AsyncIterator[str]:
        try:
            for item in self._items:
                await asyncio.sleep(self._pause)
                yield item
            if self._then_raise is not None:
                raise self._then_raise
        finally:
            self.closed = True


async def collect(stream) -> list:
    return [item async for item in stream]


async def test_items_pass_through_and_the_source_is_closed_at_the_end() -> None:
    source = Source("a", "b")

    assert await collect(with_idle_ticks(source(), every=1.0)) == ["a", "b"]
    assert source.closed


async def test_a_quiet_source_produces_idle_ticks_between_items() -> None:
    items = await collect(with_idle_ticks(Source("a", pause=0.05)(), every=0.01))

    assert items[-1] == "a"
    assert IDLE in items[:-1]


async def test_without_an_interval_there_are_no_ticks() -> None:
    assert await collect(with_idle_ticks(Source("a", pause=0.02)(), every=None)) == ["a"]


async def test_stopping_early_closes_the_source_even_while_it_waits() -> None:
    source = Source("a", "b", pause=10)

    async with aclosing(with_idle_ticks(source(), every=0.01)) as ticks:
        assert await anext(ticks) is IDLE

    assert source.closed


async def test_an_error_in_the_source_reaches_the_reader() -> None:
    source = Source("a", then_raise=ValueError("broken feed"))

    with pytest.raises(ValueError, match="broken feed"):
        await collect(with_idle_ticks(source(), every=1.0))
    assert source.closed


async def test_a_heartbeat_fills_the_silences_of_an_event_stream() -> None:
    async def frames() -> AsyncIterator[bytes]:
        await asyncio.sleep(0.05)
        yield b"event: done\n\n"

    sent = await collect(with_heartbeat(frames(), every=0.01))

    assert sent[-1] == b"event: done\n\n"
    assert set(sent[:-1]) == {SSE_HEARTBEAT}


class Client:
    def __init__(self) -> None:
        self._left = asyncio.Event()

    def leave(self) -> None:
        self._left.set()

    async def disconnected(self) -> None:
        await self._left.wait()


def cancellations() -> int:
    task = asyncio.current_task()
    assert task is not None
    return task.cancelling()


async def test_while_the_client_stays_every_item_passes_and_the_source_is_closed() -> None:
    source = Source("a", "b")

    assert await collect(cancel_on_disconnect(source(), Client().disconnected)) == ["a", "b"]
    assert source.closed


async def test_a_client_leaving_while_the_source_waits_ends_the_stream_at_once() -> None:
    source = Source("a", "b", pause=10)
    client = Client()
    asyncio.get_running_loop().call_later(0.05, client.leave)

    items = await asyncio.wait_for(collect(cancel_on_disconnect(source(), client.disconnected)), 2)

    assert items == []
    assert source.closed
    assert cancellations() == 0


async def test_a_client_leaving_between_two_items_ends_the_stream_before_the_next() -> None:
    source = Source("a", "b")
    client = Client()

    async with aclosing(cancel_on_disconnect(source(), client.disconnected)) as stream:
        assert await anext(stream) == "a"
        client.leave()
        await asyncio.sleep(0)
        assert await anext(stream, None) is None

    assert source.closed
    assert cancellations() == 0


async def test_a_cancellation_from_elsewhere_still_cancels_the_reader() -> None:
    source = Source("a", pause=10)
    reader = asyncio.create_task(collect(cancel_on_disconnect(source(), Client().disconnected)))
    await asyncio.sleep(0.01)

    reader.cancel()

    with pytest.raises(asyncio.CancelledError):
        await reader
    assert source.closed
