from dataclasses import dataclass, field
from typing import Literal

from pycraftcore.application_configuration.model.connector.base_connector import BaseConnector


@dataclass(slots=True)
class A2aConnector(BaseConnector):
    base_url: str
    timeout: int
    binding: Literal["JSONRPC", "HTTP+JSON", "GRPC"] = "JSONRPC"
    certificate: str | None = field(default=None)
