import pytest

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model import (
    ConnectorRegistry,
    DatabaseConnector,
    McpConnector,
)
from tests.application_configuration.model.connectors import (
    a2a_connector,
    database_connector,
    mcp_connector,
)


def test_registry_returns_the_typed_connector_by_name():
    registry = ConnectorRegistry({ConnectorType.database: {"db": database_connector()}})

    connector = registry.database("db")

    assert isinstance(connector, DatabaseConnector)
    assert connector.engine == "sqlite"


def test_registry_getitem_returns_the_bucket_for_a_type():
    connector = database_connector()
    registry = ConnectorRegistry({ConnectorType.database: {"db": connector}})

    assert registry[ConnectorType.database] == {"db": connector}
    assert registry[ConnectorType.api] == {}


def test_registry_returns_the_typed_a2a_connector_by_name():
    connector = a2a_connector()
    registry = ConnectorRegistry({ConnectorType.a2a: {"agent": connector}})

    assert registry.a2a("agent") is connector
    assert registry[ConnectorType.a2a] == {"agent": connector}


def test_registry_returns_the_typed_mcp_connector_by_name():
    registry = ConnectorRegistry({ConnectorType.mcp: {"tools": mcp_connector()}})

    result = registry.mcp("tools")

    assert isinstance(result, McpConnector)
    assert result.base_url == "https://mcp.test.com"


def test_registry_lookup_of_missing_connector_raises_key_error():
    with pytest.raises(KeyError):
        ConnectorRegistry().database("missing")


def test_registry_rejects_a_connector_bucketed_under_the_wrong_type():
    with pytest.raises(TypeError):
        ConnectorRegistry({ConnectorType.api: {"db": database_connector()}})
