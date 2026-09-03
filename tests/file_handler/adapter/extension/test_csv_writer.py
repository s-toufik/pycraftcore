import csv

from pycraftcore.file_handler.adapter.extension.csv.csv_writer import CsvFileWriter


def test_write_serializes_list_of_dicts_to_csv_file(tmp_path):
    file_path = tmp_path / "data.csv"

    CsvFileWriter.write(str(file_path), [{"name": "test", "value": "42"}])

    with open(file_path, newline="", encoding="utf-8") as file:
        assert list(csv.DictReader(file)) == [{"name": "test", "value": "42"}]


def test_write_creates_empty_file_for_empty_data(tmp_path):
    file_path = tmp_path / "empty.csv"

    CsvFileWriter.write(str(file_path), [])

    assert file_path.read_text() == ""
