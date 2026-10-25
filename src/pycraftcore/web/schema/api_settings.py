from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

DOCS_PATH: Final[str] = "/docs"
OPENAPI_PATH: Final[str] = f"{DOCS_PATH}/openapi.json"


@dataclass(frozen=True, slots=True)
class ApiSettings:
    title: str
    version: str = "0.1.0"
    base_path: str = ""
    docs: bool = False
    cors_origins: Sequence[str] = ()

    def __post_init__(self) -> None:
        if self.base_path and (not self.base_path.startswith("/") or self.base_path.endswith("/")):
            raise ValueError(
                f"base_path must start with '/' and must not end with '/': {self.base_path!r}"
            )

    @property
    def docs_path(self) -> str:
        return f"{self.base_path}{DOCS_PATH}"

    @property
    def openapi_path(self) -> str:
        return f"{self.base_path}{OPENAPI_PATH}"
