from typing import Protocol

from pycraftcore.application_configuration.model.configuration import (
    ApplicationConfiguration,
)


class ConfigurationReader(Protocol):
    def read(self) -> ApplicationConfiguration: ...
