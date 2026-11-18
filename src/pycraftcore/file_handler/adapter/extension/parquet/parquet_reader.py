from typing import Any

import pyarrow.parquet as pq

from pycraftcore.file_handler.port import Reader


class ParquetFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> list[dict[str, Any]]:
        return pq.read_table(file_path).to_pylist()
