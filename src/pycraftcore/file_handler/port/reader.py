from abc import ABC, abstractmethod
from typing import Any

from pycraftcore.file_handler.enum.read_chunk_mode import ReadChunkMode


class Reader(ABC):
    @classmethod
    def read(
        cls,
        file_path: str,
        read_chunk_mode: ReadChunkMode | None = None,
        start: int | None = None,
        count: int | None = None,
    ) -> Any:
        match read_chunk_mode:
            case ReadChunkMode.LINE:
                return cls._read_line_chunk(file_path, start, count)
            case _:
                return cls._read_full(file_path)

    @staticmethod
    @abstractmethod
    def _read_full(file_path: str) -> Any: ...

    @staticmethod
    def _read_line_chunk(file_path: str, start: int | None, count: int | None) -> list[str]:
        start_index = start if start is not None else 0
        stop_index = start_index + count if count is not None else None
        lines: list[str] = []
        with open(file_path, encoding="utf-8") as file:
            for index, line in enumerate(file):
                if index < start_index:
                    continue
                if stop_index is not None and index >= stop_index:
                    break
                lines.append(line)
        return lines
