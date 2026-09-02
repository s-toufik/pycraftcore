import pytest

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model.connector import (
    ApiConnector,
    ConnectorRegistry,
    DatabaseConnector,
    FileConnector,
    McpConnector,
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


def test_mcp_connector_defaults_transport_to_streamable_http_and_certificate_to_none():
    connector = McpConnector(
        name="tools",
        type=ConnectorType.mcp,
        auth=NoAuth(type=AuthType.none),
        base_url="https://mcp.test.com",
        timeout=5,
    )

    assert connector.transport == "streamable_http"
    assert connector.certificate is None


def test_mcp_connector_accepts_sse_transport():
    connector = McpConnector(
        name="tools",
        type=ConnectorType.mcp,
        auth=NoAuth(type=AuthType.none),
        base_url="https://mcp.test.com",
        timeout=5,
        transport="sse",
    )

    assert connector.transport == "sse"


def make_database_connector(name: str = "db") -> DatabaseConnector:
    return DatabaseConnector(
        name=name,
        type=ConnectorType.database,
        auth=NoAuth(type=AuthType.none),
        engine="sqlite",
        host="/var/data",
        port=0,
        default_name="main",
        pool={"max": 4},
    )


def test_registry_returns_the_typed_connector_by_name():
    registry = ConnectorRegistry({ConnectorType.database: {"db": make_database_connector()}})

    connector = registry.database("db")

    assert isinstance(connector, DatabaseConnector)
    assert connector.default_name == "main"


def test_registry_getitem_returns_the_bucket_for_a_type():
    connector = make_database_connector()
    registry = ConnectorRegistry({ConnectorType.database: {"db": connector}})

    assert registry[ConnectorType.database] == {"db": connector}
    assert registry[ConnectorType.api] == {}


def test_registry_returns_the_typed_mcp_connector_by_name():
    connector = McpConnector(
        name="tools",
        type=ConnectorType.mcp,
        auth=NoAuth(type=AuthType.none),
        base_url="https://mcp.test.com",
        timeout=5,
    )
    registry = ConnectorRegistry({ConnectorType.mcp: {"tools": connector}})

    result = registry.mcp("tools")

    assert isinstance(result, McpConnector)
    assert result.base_url == "https://mcp.test.com"


def test_registry_lookup_of_missing_connector_raises_key_error():
    registry = ConnectorRegistry()

    with pytest.raises(KeyError):
        registry.database("missing")


def test_registry_rejects_a_connector_bucketed_under_the_wrong_type():
    with pytest.raises(TypeError):
        ConnectorRegistry({ConnectorType.api: {"db": make_database_connector()}})
