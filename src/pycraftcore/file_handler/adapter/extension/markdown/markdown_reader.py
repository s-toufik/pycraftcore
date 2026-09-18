from pycraftcore.file_handler.port import Reader


class MarkdownFileReader(Reader):
    @staticmethod
    def _read_full(file_path: str) -> str:
        with open(file_path, encoding="utf-8") as file:
            return file.read()
