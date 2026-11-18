from openpyxl import Workbook

from pycraftcore.file_handler.adapter.extension.xlsx.xlsx_reader import XlsxFileReader


def test_read_parses_xlsx_file_into_list_of_dicts(tmp_path):
    file_path = tmp_path / "data.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["name", "value"])
    sheet.append(["test", 42])
    workbook.save(file_path)

    result = XlsxFileReader.read(str(file_path))

    assert result == [{"name": "test", "value": 42}]


def test_read_returns_empty_list_for_header_only_file(tmp_path):
    file_path = tmp_path / "header_only.xlsx"
    workbook = Workbook()
    workbook.active.append(["name", "value"])
    workbook.save(file_path)

    result = XlsxFileReader.read(str(file_path))

    assert result == []


def test_read_skips_fully_blank_rows(tmp_path):
    file_path = tmp_path / "with_blank_row.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["name", "value"])
    sheet.append(["test", 42])
    sheet.append([None, None])
    workbook.save(file_path)

    result = XlsxFileReader.read(str(file_path))

    assert result == [{"name": "test", "value": 42}]
