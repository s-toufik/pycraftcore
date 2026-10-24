from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from contextlib import aclosing
from typing import Final

from pycraftcore.web.streaming import Idle, with_idle_ticks

EVENT_STREAM_MEDIA_TYPE: Final[str] = "text/event-stream"
EVENT_STREAM_HEADERS: Final[Mapping[str, str]] = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}
SSE_HEARTBEAT: Final[bytes] = b": heartbeat\n\n"


async def with_heartbeat(
    frames: AsyncIterator[bytes], every: float | None
) -> AsyncGenerator[bytes]:
    async with aclosing(with_idle_ticks(frames, every)) as ticks:
        async for frame in ticks:
            yield SSE_HEARTBEAT if isinstance(frame, Idle) else frame
