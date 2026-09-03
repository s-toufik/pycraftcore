from pycraftcore.file_handler.adapter.extension.csv.csv_reader import CsvFileReader


def test_read_parses_csv_file_into_list_of_dicts(tmp_path):
    file_path = tmp_path / "data.csv"
    file_path.write_text("name,value\ntest,42\n")

    result = CsvFileReader.read(str(file_path))

    assert result == [{"name": "test", "value": "42"}]


def test_read_returns_empty_list_for_header_only_file(tmp_path):
    file_path = tmp_path / "header_only.csv"
    file_path.write_text("name,value\n")

    result = CsvFileReader.read(str(file_path))

    assert result == []


def test_read_returns_empty_list_for_empty_file(tmp_path):
    file_path = tmp_path / "empty.csv"
    file_path.write_text("")

    result = CsvFileReader.read(str(file_path))

    assert result == []
