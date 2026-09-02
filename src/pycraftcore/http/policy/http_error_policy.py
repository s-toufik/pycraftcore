import asyncio

import aiohttp
import httpx

RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})

TRANSPORT_EXCEPTIONS: tuple[type[Exception], ...] = (
    httpx.TransportError,
    aiohttp.ClientConnectionError,
    aiohttp.ServerTimeoutError,
    asyncio.TimeoutError,
)


def status_code(exception: BaseException) -> int | None:
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code

    if isinstance(exception, aiohttp.ClientResponseError):
        return exception.status

    return None


def is_retryable(exception: BaseException) -> bool:

    code = status_code(exception)
    if code is not None:
        return code in RETRYABLE_STATUS_CODES

    return isinstance(exception, TRANSPORT_EXCEPTIONS)


def is_business_error(exception: BaseException) -> bool:

    code = status_code(exception)
    return code is not None and 400 <= code < 500 and code not in RETRYABLE_STATUS_CODES