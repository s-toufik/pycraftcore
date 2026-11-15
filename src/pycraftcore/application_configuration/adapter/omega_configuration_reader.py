from pathlib import Path

from pycraftcore.application_configuration.adapter.omega_tree_reader import (
    FILE_EXTENSION,
    OmegaTreeReader,
)
from pycraftcore.application_configuration.adapter.schema import (
    ApplicationConfigurationSchema,
    MapperDomainSchema,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.model.configuration import (
    ApplicationConfiguration,
)


class OmegaConfigurationReader:
    ROOT_CONFIG_FILE_NAME = "root"
    ROOT_KEY = "application_configuration"
    FOLDERS: tuple[str, ...] = ("connector", "operation", "server")

    def __init__(self, env: RunTypeEnvironment, config_directory: Path) -> None:
        self._env = env
        self._config_directory = config_directory

    def read(self) -> ApplicationConfiguration:
        environment_directory: Path = self._config_directory / self._env.value
        tree = OmegaTreeReader(
            self._config_directory / f"{self.ROOT_CONFIG_FILE_NAME}.{FILE_EXTENSION}",
            [environment_directory / folder for folder in self.FOLDERS],
        )
        schema = ApplicationConfigurationSchema(**tree.read(self.ROOT_KEY))
        return MapperDomainSchema.map(schema)
