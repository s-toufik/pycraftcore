from dataclasses import dataclass, field
from typing import Literal

from pycraftcore.application_configuration.model.connector.base_connector import BaseConnector


@dataclass(frozen=True, slots=True)
class McpRefresh:
    interval: float = 60.0
    retry_delay: float = 5.0
    max_retry_delay: float = 60.0

    def __post_init__(self) -> None:
        if self.interval <= 0:
            raise ValueError("refresh interval must be greater than 0")
        if self.retry_delay <= 0:
            raise ValueError("refresh retry_delay must be greater than 0")
        if self.max_retry_delay < self.retry_delay:
            raise ValueError("refresh max_retry_delay must be greater than or equal to retry_delay")

    def delay_after(self, failures: int) -> float:
        if failures <= 0:
            return self.interval
        return min(self.retry_delay * 2 ** (failures - 1), self.max_retry_delay)


@dataclass(slots=True)
class McpConnector(BaseConnector):
    base_url: str
    timeout: int
    transport: Literal["sse", "streamable_http"] = "streamable_http"
    certificate: str | None = field(default=None)
    refresh: McpRefresh = field(default_factory=McpRefresh)
