from typing import Any

import yaml

from pycraftcore.file_handler.port.reader import Reader


class YmlFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> dict[str, Any]:
        with open(file_path) as file:
            return yaml.safe_load(file)
