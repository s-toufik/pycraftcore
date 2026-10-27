from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import aclosing
from functools import partial

from blacksheep import Request, Response, StreamedContent
from blacksheep.contents import ASGIContent

from pycraftcore.web.asgi import Receive
from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE
from pycraftcore.web.streaming import cancel_on_disconnect


def event_stream(frames: AsyncIterator[bytes], request: Request) -> Response:
    content = request.content
    if not isinstance(content, ASGIContent):
        raise TypeError("event_stream needs the request of an ASGI call")
    return Response(
        200,
        [(name.encode(), value.encode()) for name, value in EVENT_STREAM_HEADERS.items()],
        StreamedContent(
            EVENT_STREAM_MEDIA_TYPE.encode(), _until_disconnected(frames, content.receive)
        ),
    )


def _until_disconnected(
    frames: AsyncIterator[bytes], receive: Receive
) -> Callable[[], AsyncGenerator[bytes]]:
    async def stream() -> AsyncGenerator[bytes]:
        async with aclosing(cancel_on_disconnect(frames, partial(_client_left, receive))) as kept:
            async for frame in kept:
                yield frame

    return stream


async def _client_left(receive: Receive) -> None:
    message = await receive()
    while message["type"] != "http.disconnect":
        message = await receive()
