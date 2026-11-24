from typing import Protocol, runtime_checkable

from pycraftcore.application_configuration.model import ApplicationConfiguration


@runtime_checkable
class ConfigurationReader(Protocol):
    def read(self) -> ApplicationConfiguration: ...
