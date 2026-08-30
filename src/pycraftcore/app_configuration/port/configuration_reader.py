from typing import Protocol

from pycraftcore.app_configuration.model.configuration import AppConfiguration


class ConfigurationReader(Protocol):
    def read(self) -> AppConfiguration: ...
