import pytest

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model.connector import (
    A2aConnector,
    ApiConnector,
    ConnectorRegistry,
    DatabaseConnector,
    DatabasePool,
    FileConnector,
    McpConnector,
    McpRefresh,
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


def make_database_connector(**overrides) -> DatabaseConnector:
    values = dict(
        name="db",
        type=ConnectorType.database,
        auth=NoAuth(type=AuthType.none),
        engine="sqlite",
        host="/var/data",
        port=0,
    )
    values.update(overrides)
    return DatabaseConnector(**values)


def test_a_database_connector_waits_5_seconds_with_a_pool_of_one_by_default():
    connector = make_database_connector()

    assert connector.timeout == 5
    assert connector.pool == DatabasePool(min=1, max=1)


def test_a_database_connector_holds_its_pool():
    assert make_database_connector(pool=DatabasePool(min=2, max=4)).pool.max == 4


@pytest.mark.parametrize(
    ("pool", "message"),
    [
        ({"min": -1}, "min must be 0 or more"),
        ({"max": 0}, "max must be 1 or more"),
        ({"min": 3, "max": 2}, "greater than or equal to min"),
    ],
)
def test_a_pool_that_cannot_work_is_refused(pool, message):
    with pytest.raises(ValueError, match=message):
        DatabasePool(**pool)


def test_a_database_timeout_must_be_positive():
    with pytest.raises(ValueError, match="timeout must be greater than 0"):
        make_database_connector(timeout=0)


def test_an_a2a_connector_speaks_json_rpc_by_default():
    connector = A2aConnector(
        name="agent",
        type=ConnectorType.a2a,
        auth=NoAuth(type=AuthType.none),
        base_url="http://agent:8000/a2a",
        timeout=60,
    )

    assert connector.binding == "JSONRPC"
    assert connector.certificate is None


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


def test_registry_returns_the_typed_connector_by_name():
    registry = ConnectorRegistry({ConnectorType.database: {"db": make_database_connector()}})

    connector = registry.database("db")

    assert isinstance(connector, DatabaseConnector)
    assert connector.engine == "sqlite"


def test_registry_getitem_returns_the_bucket_for_a_type():
    connector = make_database_connector()
    registry = ConnectorRegistry({ConnectorType.database: {"db": connector}})

    assert registry[ConnectorType.database] == {"db": connector}
    assert registry[ConnectorType.api] == {}


def test_registry_returns_the_typed_a2a_connector_by_name():
    connector = A2aConnector(
        name="agent",
        type=ConnectorType.a2a,
        auth=NoAuth(type=AuthType.none),
        base_url="http://agent/a2a",
        timeout=60,
    )
    registry = ConnectorRegistry({ConnectorType.a2a: {"agent": connector}})

    assert registry.a2a("agent") is connector
    assert registry[ConnectorType.a2a] == {"agent": connector}


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


def test_mcp_connector_defaults_its_refresh_settings():
    connector = McpConnector(
        name="tools",
        type=ConnectorType.mcp,
        auth=NoAuth(type=AuthType.none),
        base_url="https://mcp.test.com",
        timeout=5,
    )

    assert connector.refresh == McpRefresh(interval=60.0, retry_delay=5.0, max_retry_delay=60.0)


@pytest.mark.parametrize(
    ("settings", "message"),
    [
        ({"interval": 0}, "interval"),
        ({"retry_delay": 0}, "retry_delay"),
        ({"retry_delay": 10, "max_retry_delay": 5}, "max_retry_delay"),
    ],
)
def test_mcp_refresh_rejects_settings_that_cannot_schedule(settings, message):
    with pytest.raises(ValueError, match=message):
        McpRefresh(**settings)
