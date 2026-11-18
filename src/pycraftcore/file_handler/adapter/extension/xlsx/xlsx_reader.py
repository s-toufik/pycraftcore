from typing import Any

from openpyxl import load_workbook

from pycraftcore.file_handler.port import Reader


class XlsxFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> list[dict[str, Any]]:
        workbook = load_workbook(file_path, read_only=True, data_only=True)
        try:
            sheet = workbook.active
            rows = sheet.iter_rows(values_only=True)
            header = next(rows, None)
            if header is None:
                return []
            columns = [str(cell) if cell is not None else "" for cell in header]
            return [
                dict(zip(columns, row, strict=False))
                for row in rows
                if any(cell is not None for cell in row)
            ]
        finally:
            workbook.close()
