from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import aclosing
from typing import Final

from blacksheep import Request, Response, StreamedContent

from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE
from pycraftcore.web.streaming import Idle, with_idle_ticks

DISCONNECT_CHECK_SECONDS: Final[float] = 1.0


def event_stream(frames: AsyncIterator[bytes], request: Request) -> Response:
    return Response(
        200,
        [(name.encode(), value.encode()) for name, value in EVENT_STREAM_HEADERS.items()],
        StreamedContent(EVENT_STREAM_MEDIA_TYPE.encode(), _until_disconnected(frames, request)),
    )


def _until_disconnected(
    frames: AsyncIterator[bytes], request: Request
) -> Callable[[], AsyncGenerator[bytes]]:
    async def stream() -> AsyncGenerator[bytes]:
        async with aclosing(with_idle_ticks(frames, DISCONNECT_CHECK_SECONDS)) as ticks:
            async for frame in ticks:
                if await request.is_disconnected():
                    return
                if not isinstance(frame, Idle):
                    yield frame

    return stream
