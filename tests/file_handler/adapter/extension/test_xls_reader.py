import xlwt

from pycraftcore.file_handler.adapter.extension.xls.xls_reader import XlsFileReader


def _write_legacy_xls(file_path, rows: list[list]) -> None:
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Sheet1")
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            sheet.write(row_index, column_index, value)
    workbook.save(str(file_path))


def test_read_parses_legacy_xls_file_into_list_of_dicts(tmp_path):
    file_path = tmp_path / "data.xls"
    _write_legacy_xls(file_path, [["name", "value"], ["test", 42]])

    result = XlsFileReader.read(str(file_path))

    assert result == [{"name": "test", "value": 42.0}]


def test_read_returns_empty_list_for_header_only_file(tmp_path):
    file_path = tmp_path / "header_only.xls"
    _write_legacy_xls(file_path, [["name", "value"]])

    result = XlsFileReader.read(str(file_path))

    assert result == []
