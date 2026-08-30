from pathlib import Path
from typing import cast, Any

from omegaconf import OmegaConf, DictConfig

from pycraftcore.app_configuration.adapter.schema import (
    AppConfigurationSchema,
    MapperDomainSchema,
)
from pycraftcore.app_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.app_configuration.model.configuration import AppConfiguration


class OmegaConfigurationReader:
    FILE_EXTENSION = "yml"
    ROOT_CONFIG_FILE_NAME = "root"
    CONNECTOR_CONFIG_FILE_NAME = "connector"
    OPERATION_CONFIG_FILE_NAME = "operation"
    CRONJOB_CONFIG_FILE_NAME = "cronjob"

    def __init__(self, env: RunTypeEnvironment, config_directory: Path) -> None:
        self._env = env
        self._config_directory = config_directory

    def read(self) -> AppConfiguration:
        config_root: Path = (
            self._config_directory / f"{self.ROOT_CONFIG_FILE_NAME}.{self.FILE_EXTENSION}"
        )
        config_dir_env = self._config_directory / f"{self._env.value}"

        omega_config: DictConfig = self._omega_read(config_dir_env, config_root)
        omega_container: Any = OmegaConf.to_container(
            omega_config.app_configuration, resolve=True, throw_on_missing=True
        )
        app_config_schema = AppConfigurationSchema(**omega_container)
        return MapperDomainSchema.map(app_config_schema)

    def _omega_read(self, config_dir_env: Path, config_root: Path) -> DictConfig:
        return cast(
            DictConfig,
            OmegaConf.merge(
                *self._load_yml_dir(config_dir_env / self.CONNECTOR_CONFIG_FILE_NAME),
                *self._load_yml_dir(config_dir_env / self.OPERATION_CONFIG_FILE_NAME),
                *self._load_yml_dir(config_dir_env / self.CRONJOB_CONFIG_FILE_NAME),
                OmegaConf.load(config_root),
            ),
        )

    def _load_yml_dir(self, directory: Path) -> list:
        return [OmegaConf.load(f) for f in sorted(directory.glob(f"*.{self.FILE_EXTENSION}"))]
