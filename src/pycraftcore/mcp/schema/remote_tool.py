from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RemoteTool:
    name: str
    description: str = ""
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
