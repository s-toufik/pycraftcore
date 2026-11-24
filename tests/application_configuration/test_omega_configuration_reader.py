import os
from pathlib import Path
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

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
from pycraftcore.application_configuration.enum.server_type import ServerType
from pycraftcore.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from pycraftcore.logger.enum.log_level import LogLevel

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
    "OTEL_HOST",
    "OTEL_PORT",
)
MISSING_ENV_VARS = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]


def test_read_merges_the_environment_folders_under_the_root_file():
    config_dir = Path("/fake/config")
    reader = OmegaConfigurationReader(RunTypeEnvironment.debug, config_dir)

    with patch(
        "pycraftcore.application_configuration.adapter.omega_configuration_reader.OmegaTreeReader"
    ) as tree_reader:
        tree_reader.return_value.read.return_value = {
            "env": "debug",
            "run": "async",
            "log": "INFO",
            "server": {},
            "connector": {},
            "operation": {},
        }
        result = reader.read()

    environment = config_dir / "debug"
    tree_reader.assert_called_once_with(
        config_dir / "root.yml",
        [environment / "connector", environment / "operation", environment / "server"],
    )
    tree_reader.return_value.read.assert_called_once_with("application_configuration")
    assert isinstance(result, ApplicationConfiguration)
    assert (result.env, result.run) == (RunTypeEnvironment.debug, RunTypeApplication.asynchronous)


def test_omega_read_merges_real_yml_files_from_disk(tmp_path):
    env_dir = tmp_path / "debug"
    (env_dir / "connector").mkdir(parents=True)
    (env_dir / "operation").mkdir(parents=True)
    (env_dir / "connector" / "db.yml").write_text("connector:\n  database:\n    users: {}\n")
    (tmp_path / "root.yml").write_text(
        "application_configuration:\n"
        "  env: debug\n"
        "  run: async\n"
        "  log: INFO\n"
        "  server: {}\n"
        "  connector: {}\n"
        "  operation: {}\n"
    )

    reader = OmegaConfigurationReader(RunTypeEnvironment.debug, tmp_path)

    result = reader.read()

    assert isinstance(result, ApplicationConfiguration)
    assert result.env == RunTypeEnvironment.debug


def test_server_files_are_merged_and_read_as_asgi_servers(tmp_path, monkeypatch):
    monkeypatch.setenv("ORDERS_API_BASE_PATH", "/orders-api")
    (tmp_path / "debug" / "server").mkdir(parents=True)
    (tmp_path / "debug" / "server" / "asgi.yml").write_text(
        "server:\n"
        "  orders-api:\n"
        "    name: orders-api\n"
        "    type: asgi\n"
        "    docs: true\n"
        '    base_path: ${oc.env:ORDERS_API_BASE_PATH,""}\n'
    )
    (tmp_path / "root.yml").write_text(
        "application_configuration:\n"
        "  env: debug\n"
        "  run: async\n"
        "  log: WARNING\n"
        "  server:\n"
        "    asgi:\n"
        "      orders-api: ${server.orders-api}\n"
        "  connector: {}\n"
        "  operation: {}\n"
    )

    result = OmegaConfigurationReader(RunTypeEnvironment.debug, tmp_path).read()

    assert result.log is LogLevel.WARNING
    assert result.server.asgi("orders-api").base_path == "/orders-api"
    assert result.server.asgi("orders-api").docs is True


def test_wrapped_mcp_tools_survive_the_yaml_tree_with_their_fixed_arguments(tmp_path, monkeypatch):
    monkeypatch.setenv("KITCHEN_DB", "kitchen")
    (tmp_path / "debug" / "connector").mkdir(parents=True)
    (tmp_path / "debug" / "operation").mkdir(parents=True)
    (tmp_path / "debug" / "connector" / "mcp.yml").write_text(
        "connector:\n"
        "  self:\n"
        "    name: toolbox\n"
        "    type: mcp\n"
        "    base_url: http://toolbox/mcp\n"
        "    timeout: 30\n"
        "    auth:\n"
        "      type: none\n"
    )
    (tmp_path / "debug" / "operation" / "scope.yml").write_text(
        "operation:\n"
        "  scope_kitchen:\n"
        "    name: kitchen\n"
        "    type: mcp\n"
        "    connector: ${connector.self}\n"
        "    tools:\n"
        "      - python_executor\n"
        "      - name: recipes_find\n"
        "        tool: mongodb_find\n"
        "        arguments:\n"
        "          database: ${oc.env:KITCHEN_DB}\n"
        "          collection: recipes\n"
        "          limit: 20\n"
    )
    (tmp_path / "root.yml").write_text(
        "application_configuration:\n"
        "  env: debug\n"
        "  run: async\n"
        "  log: INFO\n"
        "  server: {}\n"
        "  connector:\n"
        "    mcp:\n"
        "      self: ${connector.self}\n"
        "  operation:\n"
        "    scope_kitchen: ${operation.scope_kitchen}\n"
    )

    kitchen = (
        OmegaConfigurationReader(RunTypeEnvironment.debug, tmp_path)
        .read()
        .operation.mcp("scope_kitchen")
    )

    assert kitchen.listed_tools == ("python_executor",)
    (recipes,) = kitchen.wrapped_tools
    assert recipes.arguments == {"database": "kitchen", "collection": "recipes", "limit": 20}


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
    assert result.server[ServerType.asgi]
    assert result.connector[ConnectorType.file]
    assert result.connector[ConnectorType.telemetry]
    assert result.operation
    assert result.operation.mcp

    database_connector = next(iter(result.connector[ConnectorType.database].values()))
    assert database_connector.host == os.environ["DB_HOST"]
    assert database_connector.auth.username == os.environ["DB_USER"]
    assert database_connector.auth.password == os.environ["DB_PASSWORD"]
    orders = result.operation.database("dummy_database_op")
    assert orders.database == os.environ["DB_NAME"]
    assert orders.connector == database_connector
    assert orders.collection("events") == "order_events"
    assert result.operation.a2a("dummy_a2a_op").connector == result.connector.a2a("agent")

    api_auths = [connector.auth for connector in result.connector[ConnectorType.api].values()]
    assert any(getattr(auth, "key_value", None) == os.environ["API_KEY"] for auth in api_auths)
    assert any(
        getattr(auth, "username", None) == os.environ["API_USERNAME"]
        and getattr(auth, "password", None) == os.environ["API_PASSWORD"]
        for auth in api_auths
    )
