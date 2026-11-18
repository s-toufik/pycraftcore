from typing import Any

from openpyxl import Workbook

from pycraftcore.file_handler.port import Writer


class XlsxFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: list[dict[str, Any]]) -> None:
        workbook = Workbook()
        sheet = workbook.active
        if data:
            columns = list(data[0].keys())
            sheet.append(columns)
            for row in data:
                sheet.append([row.get(column) for column in columns])
        workbook.save(file_path)
