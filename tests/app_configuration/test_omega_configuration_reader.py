from pathlib import Path
from unittest.mock import MagicMock, patch

from omegaconf import DictConfig, OmegaConf

from pycraftcore.application_configuration.adapter.omega_configuration_reader import (
    OmegaConfigurationReader,
)
from pycraftcore.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.model.configuration import ApplicationConfiguration


@patch(
    "pycraftcore.application_configuration.adapter.omega_configuration_reader.MapperDomainSchema.map"
)
@patch(
    "pycraftcore.application_configuration.adapter.omega_configuration_reader.ApplicationConfigurationSchema"
)
@patch(
    "pycraftcore.application_configuration.adapter.omega_configuration_reader.OmegaConf.to_container"
)
def test_read_orchestration(mock_to_container, mock_schema, mock_mapper):
    env = RunTypeEnvironment.production
    config_dir = Path("/fake/config")
    reader = OmegaConfigurationReader(env, config_dir)
    fake_dict_config = MagicMock(spec=DictConfig)
    fake_dict_config.application_configuration = MagicMock()
    fake_app_configuration = MagicMock()

    expected_container = {"name": "test-app"}

    expected_result = MagicMock()

    mock_to_container.return_value = expected_container
    mock_schema.return_value = fake_app_configuration
    mock_mapper.return_value = expected_result

    with patch.object(reader, "_omega_read", return_value=fake_dict_config) as mock_omega_read:
        result = reader.read()
        assert result == expected_result

        mock_omega_read.assert_called_once_with(
            config_dir / "prod",
            config_dir / "root.yml",
        )

        mock_to_container.assert_called_once_with(
            fake_dict_config.application_configuration,
            resolve=True,
            throw_on_missing=True,
        )

        mock_schema.assert_called_once_with(**expected_container)
        mock_mapper.assert_called_once_with(fake_app_configuration)


def test_read_validation_schema():

    reader = OmegaConfigurationReader(
        RunTypeEnvironment.production,
        Path("/fake/config"),
    )

    fake_dict_config = OmegaConf.create(
        {
            "application_configuration": {
                "env": "debug",
                "run": "async",
                "connector": {},
                "operation": {},
                "cronjob": [],
            }
        }
    )

    with patch.object(
        reader,
        "_omega_read",
        return_value=fake_dict_config,
    ):
        result = reader.read()
        assert isinstance(result, ApplicationConfiguration)
        assert result.env == RunTypeEnvironment.debug
        assert result.run == RunTypeApplication.asynchronous


def test_omega_read_merges_real_yml_files_from_disk(tmp_path):
    env_dir = tmp_path / "debug"
    (env_dir / "connector").mkdir(parents=True)
    (env_dir / "operation").mkdir(parents=True)
    (env_dir / "cronjob").mkdir(parents=True)
    (env_dir / "connector" / "db.yml").write_text("connector:\n  database:\n    users: {}\n")
    (tmp_path / "root.yml").write_text(
        "application_configuration:\n  env: debug\n  run: async\n  connector: {}\n  operation: {}\n  cronjob: []\n"
    )

    reader = OmegaConfigurationReader(RunTypeEnvironment.debug, tmp_path)

    result = reader.read()

    assert isinstance(result, ApplicationConfiguration)
    assert result.env == RunTypeEnvironment.debug
