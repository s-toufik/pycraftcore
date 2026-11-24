from dataclasses import dataclass, field
from typing import Any

from pycraftcore.application_configuration.model.server.base_server import BaseServer


@dataclass(slots=True)
class AsgiServer(BaseServer):
    base_path: str = ""
    docs: bool = False
    cors_origins: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
