from pycraftcore.file_handler.port import Writer


class MarkdownFileWriter(Writer):
    @staticmethod
    def write(file_path: str, data: dict[str, str]) -> None:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(next(iter(data.values()), ""))
