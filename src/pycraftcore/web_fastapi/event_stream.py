from collections.abc import AsyncIterable

from fastapi.responses import StreamingResponse

from pycraftcore.web.sse import EVENT_STREAM_HEADERS, EVENT_STREAM_MEDIA_TYPE


class EventStreamResponse(StreamingResponse):
    media_type = EVENT_STREAM_MEDIA_TYPE


def event_stream(frames: AsyncIterable[bytes]) -> EventStreamResponse:
    return EventStreamResponse(frames, headers=dict(EVENT_STREAM_HEADERS))
