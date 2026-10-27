import asyncio
import contextlib
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from typing import Any, Final


class Idle: ...


class _End: ...


IDLE: Final[Idle] = Idle()
_END: Final[_End] = _End()


async def with_idle_ticks[T](
    source: AsyncIterator[T], every: float | None
) -> AsyncGenerator[T | Idle]:
    pending: asyncio.Task[T | _End] | None = None
    try:
        while True:
            pending = pending or asyncio.create_task(_next(source))
            done, _ = await asyncio.wait({pending}, timeout=every)
            if not done:
                yield IDLE
                continue
            item = pending.result()
            pending = None
            if isinstance(item, _End):
                return
            yield item
    finally:
        if pending is not None and not pending.done():
            pending.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await pending
        await _close(source)


async def cancel_on_disconnect[T](
    source: AsyncIterator[T], disconnected: Callable[[], Awaitable[object]]
) -> AsyncGenerator[T]:
    reader = _Reader(_running_task())
    watcher = asyncio.create_task(reader.stop_when(disconnected))
    try:
        while not reader.stopped:
            item = await reader.next(source)
            if isinstance(item, _End):
                return
            yield item
    finally:
        watcher.cancel()
        reader.release()
        await _close(source)


class _Reader:
    def __init__(self, task: asyncio.Task[Any]) -> None:
        self._task = task
        self._waiting = False
        self._cancelled = False
        self.stopped = False

    async def next[T](self, source: AsyncIterator[T]) -> T | _End:
        self._waiting = True
        try:
            return await anext(source, _END)
        except asyncio.CancelledError:
            if not self._cancelled:
                raise
            self._cancelled = False
            if self._task.uncancel():
                raise
            return _END
        finally:
            self._waiting = False

    async def stop_when(self, disconnected: Callable[[], Awaitable[object]]) -> None:
        await disconnected()
        self.stopped = True
        if self._waiting:
            self._cancelled = True
            self._task.cancel()

    def release(self) -> None:
        if self._cancelled:
            self._cancelled = False
            self._task.uncancel()


def _running_task() -> asyncio.Task[Any]:
    task = asyncio.current_task()
    if task is None:
        raise RuntimeError("cancel_on_disconnect must be read by an asyncio task")
    return task


async def _next[T](source: AsyncIterator[T]) -> T | _End:
    return await anext(source, _END)


async def _close(source: AsyncIterator[Any]) -> None:
    if isinstance(source, AsyncGenerator):
        await source.aclose()
