from collections.abc import AsyncIterable

from litestar.response import Stream

from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE


def event_stream(frames: AsyncIterable[bytes]) -> Stream:
    return Stream(frames, media_type=EVENT_STREAM_MEDIA_TYPE, headers=dict(EVENT_STREAM_HEADERS))
