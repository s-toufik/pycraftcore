from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel

type HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class ResponseKind(StrEnum):
    JSON = "json"
    EVENT_STREAM = "event_stream"


@dataclass(frozen=True, slots=True)
class HttpResult:
    body: BaseModel
    status_code: int


@dataclass(frozen=True, slots=True)
class HttpRoute:
    method: HttpMethod
    path: str
    handler: Callable[..., Awaitable[Any]]
    body: type[BaseModel] | None = None
    response: type[BaseModel] | None = None
    kind: ResponseKind = ResponseKind.JSON
    status_code: int = 200
    tags: tuple[str, ...] = ()
