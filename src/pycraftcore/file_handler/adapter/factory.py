from pathlib import Path
from typing import Any

from pycraftcore.file_handler.adapter.strategy import FileHandlerStrategy


class FileHandlerFactory:
    def __init__(self, file_path: str, strategy: FileHandlerStrategy) -> None:
        self._file_path = Path(file_path)
        self._strategy = strategy

    def _file_extension(self) -> str:
        return self._file_path.suffix.lstrip(".")

    def _validate_file_for_read(self) -> None:
        if not self._file_path.exists():
            raise FileNotFoundError(f"File not found at {self._file_path}")

        if not self._strategy.supports(self._file_extension()):
            raise NotImplementedError(f"File extension not supported: {self._file_extension()}")

    def _validate_file_for_write(self) -> None:
        if not self._file_path.parent.exists():
            raise FileNotFoundError(f"File location not found at {self._file_path}")

        if not self._strategy.supports(self._file_extension()):
            raise NotImplementedError(f"File extension not supported: {self._file_extension()}")

    def read(self) -> dict[str, Any]:
        self._validate_file_for_read()
        reader = self._strategy.get_reader(self._file_extension())
        return reader.read(str(self._file_path))

    def write(self, data: Any) -> None:
        self._validate_file_for_write()
        writer = self._strategy.get_writer(self._file_extension())
        writer.write(str(self._file_path), data)
