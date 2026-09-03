import csv
from typing import Any

from pycraftcore.file_handler.port import Writer


class CsvFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: list[dict[str, Any]]) -> None:
        if not data:
            with open(file_path, "w", newline="", encoding="utf-8"):
                return

        fieldnames = data[0].keys()

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
