import csv
from typing import Any

from pycraftcore.file_handler.port import Reader

_CANDIDATE_DELIMITERS: str = ",;\t|"


class CsvFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> list[dict[str, Any]]:
        with open(file_path, newline="", encoding="utf-8") as file:
            sample = file.read(4096)
            file.seek(0)
            return list(csv.DictReader(file, dialect=_sniff_dialect(sample)))


def _sniff_dialect(sample: str) -> type[csv.Dialect] | csv.Dialect:
    if not sample.strip():
        return csv.excel
    try:
        return csv.Sniffer().sniff(sample, delimiters=_CANDIDATE_DELIMITERS)
    except csv.Error:
        return csv.excel
