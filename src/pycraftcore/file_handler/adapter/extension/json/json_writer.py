from typing import Any

import orjson

from pycraftcore.file_handler.port import Writer


class JsonFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: dict[str, Any]) -> None:
        with open(file_path, "wb") as file:
            file.write(orjson.dumps(data))
