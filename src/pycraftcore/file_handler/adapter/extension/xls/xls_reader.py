from typing import Any

import xlrd

from pycraftcore.file_handler.port import Reader


class XlsFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> list[dict[str, Any]]:
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(0)
        if sheet.nrows == 0:
            return []
        columns = [str(cell) for cell in sheet.row_values(0)]
        return [
            dict(zip(columns, sheet.row_values(row_index), strict=False))
            for row_index in range(1, sheet.nrows)
        ]
