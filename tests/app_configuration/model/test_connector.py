from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model.connector import (
    ApiConnector,
    DatabaseConnector,
    FileConnector,
    TelemetryConnector,
)
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.no_auth import NoAuth


def test_api_connector_defaults_certificate_to_none():
    connector = ApiConnector(
        name="llm",
        type=ConnectorType.api,
        auth=NoAuth(type=AuthType.none),
        base_url="https://api.test.com",
        timeout=30,
        retry=3,
    )

    assert connector.certificate is None


def test_database_connector_holds_pool_settings():
    connector = DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=NoAuth(type=AuthType.none),
        engine="sqlite",
        host="/var/data",
        port=0,
        default_name="main",
        pool={"max": 4},
    )

    assert connector.pool == {"max": 4}


def test_file_connector_holds_base_path():
    connector = FileConnector(
        name="files",
        type=ConnectorType.file,
        auth=NoAuth(type=AuthType.none),
        base_path="/var/files",
    )

    assert connector.base_path == "/var/files"


def test_telemetry_connector_holds_host_and_port():
    connector = TelemetryConnector(
        name="otel",
        type=ConnectorType.telemetry,
        auth=NoAuth(type=AuthType.none),
        host="collector",
        port=4317,
    )

    assert connector.host == "collector"
    assert connector.port == 4317
