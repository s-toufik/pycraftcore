from typing import Any, Protocol

from pycraftcore.file_handler.enum.read_chunk_mode import ReadChunkMode
from pycraftcore.file_handler.schema.file_manifest import FileManifest


class FileHandlerFactory(Protocol):
    def read(
        self,
        read_chunk_mode: ReadChunkMode | None = None,
        start: int | None = None,
        count: int | None = None,
    ) -> Any: ...

    def write(self, data: Any) -> None: ...

    def manifest(self) -> FileManifest: ...
