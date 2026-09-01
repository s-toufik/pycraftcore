import traceback
from typing import ParamSpec

from pycraftcore.application_configuration.model.configuration import ApplicationConfiguration
from pycraftcore.application_configuration.port.configuration_reader import (
    ConfigurationReader,
)
from pycraftcore.logger.port.logger import Logger

P = ParamSpec("P")


class LoadApplicationConfiguration:

    def __init__(self, configuration_reader: ConfigurationReader, logger: Logger):
        self._configuration_reader = configuration_reader
        self._logger = logger

    def load(self) -> ApplicationConfiguration | None:
        try:
            configuration: ApplicationConfiguration = self._configuration_reader.read()
            self._logger.info(f"Configuration loaded successfully")
            return configuration
        except Exception as exception:
            traceback_str: str = "".join(traceback.format_exception(exception))
            self._logger.critical(f"Configuration could not be read : {traceback_str}")
            raise exception

