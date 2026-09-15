from typing import Any

from pycraftcore.file_handler.port import Reader


class TxtFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> Any:
        with open(file_path, encoding="utf-8") as file:
            return file.read()
