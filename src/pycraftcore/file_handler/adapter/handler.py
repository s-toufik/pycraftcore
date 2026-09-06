from pycraftcore.file_handler.adapter.extension.csv.csv_reader import CsvFileReader
from pycraftcore.file_handler.adapter.extension.csv.csv_writer import CsvFileWriter
from pycraftcore.file_handler.adapter.extension.json.json_reader import JsonFileReader
from pycraftcore.file_handler.adapter.extension.json.json_writer import JsonFileWriter
from pycraftcore.file_handler.adapter.extension.markdown.markdown_reader import MarkdownFileReader
from pycraftcore.file_handler.adapter.extension.markdown.markdown_writer import MarkdownFileWriter
from pycraftcore.file_handler.adapter.extension.yml.yml_reader import YmlFileReader
from pycraftcore.file_handler.adapter.extension.yml.yml_writer import YmlFileWriter
from pycraftcore.file_handler.adapter.provider import FileHandlerProvider
from pycraftcore.file_handler.adapter.strategy import FileHandlerStrategy

yml_file_reader = YmlFileReader()
yml_file_writer = YmlFileWriter()


strategy = FileHandlerStrategy(
    {
        "yml": {"reader": yml_file_reader, "writer": yml_file_writer},
        "yaml": {"reader": yml_file_reader, "writer": yml_file_writer},
        "json": {"reader": JsonFileReader(), "writer": JsonFileWriter()},
        "csv": {"reader": CsvFileReader(), "writer": CsvFileWriter()},
        "md": {"reader": MarkdownFileReader(), "writer": MarkdownFileWriter()},
    }
)

Handler = FileHandlerProvider(strategy)
