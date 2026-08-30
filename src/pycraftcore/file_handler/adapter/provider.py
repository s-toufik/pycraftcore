from pycraftcore.file_handler.adapter.factory import FileHandlerFactory
from pycraftcore.file_handler.adapter.strategy import FileHandlerStrategy


class FileHandlerProvider:
    def __init__(self, strategy: FileHandlerStrategy) -> None:
        self._strategy = strategy

    def __call__(self, file_path: str) -> FileHandlerFactory:
        return FileHandlerFactory(file_path, self._strategy)
