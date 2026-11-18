from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from pycraftcore.file_handler.port import Writer


class ParquetFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: list[dict[str, Any]]) -> None:
        pq.write_table(pa.Table.from_pylist(data), file_path)
