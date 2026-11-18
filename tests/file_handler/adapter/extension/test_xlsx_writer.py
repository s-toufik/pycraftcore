from openpyxl import load_workbook

from pycraftcore.file_handler.adapter.extension.xlsx.xlsx_writer import XlsxFileWriter


def test_write_serializes_list_of_dicts_to_xlsx_file(tmp_path):
    file_path = tmp_path / "data.xlsx"

    XlsxFileWriter.write(str(file_path), [{"name": "test", "value": 42}])

    workbook = load_workbook(file_path)
    rows = list(workbook.active.iter_rows(values_only=True))
    assert rows == [("name", "value"), ("test", 42)]


def test_write_creates_empty_sheet_for_empty_data(tmp_path):
    file_path = tmp_path / "empty.xlsx"

    XlsxFileWriter.write(str(file_path), [])

    workbook = load_workbook(file_path)
    assert list(workbook.active.iter_rows(values_only=True)) == []
