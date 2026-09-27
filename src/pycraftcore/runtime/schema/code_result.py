import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CodeResult:
    type_name: str
    value: Any
    printed: str = ""

    @classmethod
    def from_stdout(cls, stdout: str) -> CodeResult:
        printed, _, envelope = stdout.rstrip("\n").rpartition("\n")
        payload: dict[str, Any] = json.loads(envelope)

        return cls(type_name=payload["__type__"], value=payload["result"], printed=printed)
