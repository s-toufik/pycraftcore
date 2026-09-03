from typing import Protocol

from pycraftcore.file_handler.port import FileHandlerFactory


class FileHandlerProvider(Protocol):
    def __call__(self, file_path: str) -> FileHandlerFactory: ...
