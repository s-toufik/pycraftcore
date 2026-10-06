from pycraftcore.file_handler.port import Writer


class SvgFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: str) -> None:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(data)
