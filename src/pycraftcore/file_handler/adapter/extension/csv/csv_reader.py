import csv
from typing import Any

from pycraftcore.file_handler.port import Reader


class CsvFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> list[dict[str, Any]]:
        with open(file_path, newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
