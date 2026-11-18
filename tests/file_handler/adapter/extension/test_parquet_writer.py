import pyarrow.parquet as pq

from pycraftcore.file_handler.adapter.extension.parquet.parquet_writer import ParquetFileWriter


def test_write_serializes_list_of_dicts_to_parquet_file(tmp_path):
    file_path = tmp_path / "data.parquet"

    ParquetFileWriter.write(str(file_path), [{"name": "test", "value": 42}])

    assert pq.read_table(str(file_path)).to_pylist() == [{"name": "test", "value": 42}]
