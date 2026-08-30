from typing import TypedDict

from pycraftcore.file_handler.port.reader import Reader
from pycraftcore.file_handler.port.writer import Writer


class FileHandlerDict(TypedDict):
    reader: Reader
    writer: Writer


class FileHandlerStrategy:
    def __init__(self, handlers: dict[str, FileHandlerDict]) -> None:
        self._handlers = handlers

    def get_reader(self, extension: str) -> Reader:
        return self._handlers[extension]["reader"]

    def get_writer(self, extension: str) -> Writer:
        return self._handlers[extension]["writer"]

    def supports(self, extension: str) -> bool:
        return extension in self._handlers
