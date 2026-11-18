from typing import Any

from pycraftcore.file_handler.port import Writer


class XlsFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: Any) -> None:
        raise NotImplementedError("Writing legacy .xls files isn't supported; write .xlsx instead")
