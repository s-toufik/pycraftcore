from typing import Any, Protocol


class FileHandlerFactory(Protocol):
    def read(self) -> dict[str, Any]: ...

    def write(self, data: Any) -> None: ...
