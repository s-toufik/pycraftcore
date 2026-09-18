from pycraftcore.file_handler.port import Writer


class TxtFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: str) -> None:
        with open(file_path, mode="w", encoding="utf-8") as file:
            file.write(data)
