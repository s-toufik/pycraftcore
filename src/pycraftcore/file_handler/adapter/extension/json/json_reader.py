import orjson
from typing import Any

from pycraftcore.file_handler.port import Reader


class JsonFileReader(Reader):
    @staticmethod
    def read(file_path: str) -> dict[str, Any]:
        with open(file_path) as file:
            return orjson.loads(file.read())
