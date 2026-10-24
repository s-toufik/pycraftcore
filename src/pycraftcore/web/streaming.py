import asyncio
import contextlib
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Final


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
        if isinstance(source, AsyncGenerator):
            await source.aclose()


async def _next[T](source: AsyncIterator[T]) -> T | _End:
    return await anext(source, _END)
