import pyarrow as pa
import pyarrow.parquet as pq

from pycraftcore.file_handler.adapter.extension.parquet.parquet_reader import ParquetFileReader


def test_read_parses_parquet_file_into_list_of_dicts(tmp_path):
    file_path = tmp_path / "data.parquet"
    pq.write_table(pa.Table.from_pylist([{"name": "test", "value": 42}]), str(file_path))

    result = ParquetFileReader.read(str(file_path))

    assert result == [{"name": "test", "value": 42}]


def test_read_returns_empty_list_for_empty_table(tmp_path):
    file_path = tmp_path / "empty.parquet"
    pq.write_table(
        pa.Table.from_pylist([], schema=pa.schema([("name", pa.string())])), str(file_path)
    )

    result = ParquetFileReader.read(str(file_path))

    assert result == []
