from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CallResult:
    content: tuple[str, ...] = ()
    structured: dict[str, Any] | None = None
    is_error: bool = False

    @property
    def text(self) -> str:
        return "\n".join(self.content)
