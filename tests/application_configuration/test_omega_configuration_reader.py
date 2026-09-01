import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf

from pycraftcore.application_configuration.adapter.omega_configuration_reader import (
    OmegaConfigurationReader,
)
from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.application_configuration.model.configuration import (
    ApplicationConfiguration,
)

load_dotenv()

REQUIRED_ENV_VARS = (
    "APP_ENV",
    "CONFIGURATION_DIR",
    "API_KEY",
    "API_USERNAME",
    "API_PASSWORD",
    "DB_HOST",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
)
MISSING_ENV_VARS = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]


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
    env = RunTypeEnvironment.debug
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
            config_dir / "debug",
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
        RunTypeEnvironment.debug,
        Path("/fake/config"),
    )

    fake_dict_config = OmegaConf.create(
        {
            "application_configuration": {
                "env": "debug",
                "run": "async",
                "connector": {},
                "operation": {},
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
    (env_dir / "connector" / "db.yml").write_text("connector:\n  database:\n    users: {}\n")
    (tmp_path / "root.yml").write_text(
        "application_configuration:\n  env: debug\n  run: async\n  connector: {}\n  operation: {}\n"
    )

    reader = OmegaConfigurationReader(RunTypeEnvironment.debug, tmp_path)

    result = reader.read()

    assert isinstance(result, ApplicationConfiguration)
    assert result.env == RunTypeEnvironment.debug


@pytest.mark.skipif(
    bool(MISSING_ENV_VARS),
    reason=f"missing required environment variables: {', '.join(MISSING_ENV_VARS)}",
)
def test_reads_real_project_config_from_environment():
    env = RunTypeEnvironment(os.environ["APP_ENV"])
    config_dir = Path(os.environ["CONFIGURATION_DIR"])

    result = OmegaConfigurationReader(env, config_dir).read()

    assert isinstance(result, ApplicationConfiguration)
    assert result.env == env
    assert result.run == RunTypeApplication.asynchronous
    assert result.connector[ConnectorType.file]
    assert result.connector[ConnectorType.telemetry]
    assert result.operation

    database_connector = next(iter(result.connector[ConnectorType.database].values()))
    assert database_connector.host == os.environ["DB_HOST"]
    assert database_connector.default_name == os.environ["DB_NAME"]
    assert database_connector.auth.username == os.environ["DB_USER"]
    assert database_connector.auth.password == os.environ["DB_PASSWORD"]

    api_auths = [connector.auth for connector in result.connector[ConnectorType.api].values()]
    assert any(getattr(auth, "key_value", None) == os.environ["API_KEY"] for auth in api_auths)
    assert any(
        getattr(auth, "username", None) == os.environ["API_USERNAME"]
        and getattr(auth, "password", None) == os.environ["API_PASSWORD"]
        for auth in api_auths
    )
