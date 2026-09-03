from pycraftcore.file_handler.adapter.extension.csv.csv_reader import CsvFileReader
from pycraftcore.file_handler.adapter.extension.csv.csv_writer import CsvFileWriter
from pycraftcore.file_handler.adapter.extension.json.json_reader import JsonFileReader
from pycraftcore.file_handler.adapter.extension.json.json_writer import JsonFileWriter
from pycraftcore.file_handler.adapter.extension.yml.yml_reader import YmlFileReader
from pycraftcore.file_handler.adapter.extension.yml.yml_writer import YmlFileWriter
from pycraftcore.file_handler.adapter.provider import FileHandlerProvider
from pycraftcore.file_handler.adapter.strategy import FileHandlerStrategy

strategy = FileHandlerStrategy(
    {
        "yml": {"reader": YmlFileReader(), "writer": YmlFileWriter()},
        "json": {"reader": JsonFileReader(), "writer": JsonFileWriter()},
        "csv": {"reader": CsvFileReader(), "writer": CsvFileWriter()},
    }
)

Handler = FileHandlerProvider(strategy)
