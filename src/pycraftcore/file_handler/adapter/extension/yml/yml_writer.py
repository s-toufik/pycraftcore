from typing import Any

import yaml

from pycraftcore.file_handler.port.writer import Writer


class YmlFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: dict[str, Any]) -> None:
        with open(file_path, "w") as file:
            yaml.dump(data, file)
