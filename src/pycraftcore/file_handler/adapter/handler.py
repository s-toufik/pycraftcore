from pycraftcore.file_handler.adapter.provider import FileHandlerProvider
from pycraftcore.file_handler.adapter.strategy import FileHandlerStrategy
from pycraftcore.file_handler.adapter.extension.yml_reader import YmlFileReader
from pycraftcore.file_handler.adapter.extension.yml_writer import YmlFileWriter

strategy = FileHandlerStrategy(
    {
        "yml": {"reader": YmlFileReader(), "writer": YmlFileWriter()},
    }
)

Handler = FileHandlerProvider(strategy)
