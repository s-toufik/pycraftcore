import orjson
from typing import Any

from pycraftcore.file_handler.port import Reader


class JsonFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> dict[str, Any]:
        with open(file_path) as file:
            return orjson.loads(file.read())
