import threading
from typing import ParamSpec

from pycraftcore.application_configuration.model.configuration import ApplicationConfiguration
from pycraftcore.application_configuration.port.configuration_reader import (
    ConfigurationReader,
)
from pycraftcore.logger.port.logger import Logger

P = ParamSpec("P")


class LoadApplicationConfiguration:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args: P.args, **kwargs: P.kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, configuration_reader: ConfigurationReader, logger: Logger):
        self._configuration_reader = configuration_reader
        self._logger = logger
        self._cached_config: ApplicationConfiguration | None = None

    def load(self) -> ApplicationConfiguration | None:
        if self._cached_config is None:
            try:
                self._cached_config = self._configuration_reader.read()
            except Exception as exception:
                self._logger.critical(exception.__str__())
        return self._cached_config

    def reload(self) -> ApplicationConfiguration | None:
        with self._lock:
            configuration = self._configuration_reader.read()
        self._cached_config = configuration
        return self._cached_config
