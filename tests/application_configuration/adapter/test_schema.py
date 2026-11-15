import pytest
from pydantic import ValidationError

from pycraftcore.application_configuration.adapter.schema import (
    ApplicationConfigurationSchema,
    MapperDomainSchema,
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
from pycraftcore.application_configuration.enum.server_type import ServerType
from pycraftcore.application_configuration.model.connector import McpConnector, McpRefresh
from pycraftcore.application_configuration.model.server import AsgiServer
from pycraftcore.logger.enum.log_level import LogLevel


REQUIRED = {
    "env": RunTypeEnvironment.debug,
    "run": RunTypeApplication.asynchronous,
    "log": LogLevel.INFO,
    "server": {},
    "connector": {},
    "operation": {},
}


def test_map_converts_schema_into_domain_model():
    schema = ApplicationConfigurationSchema(**REQUIRED)

    result = MapperDomainSchema.map(schema)

    assert isinstance(result, ApplicationConfiguration)
    assert result.env == RunTypeEnvironment.debug
    assert result.run == RunTypeApplication.asynchronous
    assert result.log is LogLevel.INFO
    assert result.server[ServerType.asgi] == {}
    assert result.connector.by_type == {}
    assert result.operation.by_name == {}


def test_mcp_connector_dict_resolves_to_mcp_connector_via_the_type_discriminator():
    schema = ApplicationConfigurationSchema(
        **REQUIRED
        | {
            "connector": {
                ConnectorType.mcp: {
                    "tools": {
                        "name": "tools",
                        "type": "mcp",
                        "auth": {"type": "none"},
                        "base_url": "https://mcp.test.com",
                        "timeout": 5,
                    }
                }
            }
        }
    )

    result = MapperDomainSchema.map(schema)
    connector = result.connector.mcp("tools")

    assert isinstance(connector, McpConnector)
    assert connector.base_url == "https://mcp.test.com"
    assert connector.transport == "streamable_http"


def test_mcp_connector_reads_refresh_settings_given_as_strings():
    schema = ApplicationConfigurationSchema(
        **REQUIRED
        | {
            "connector": {
                ConnectorType.mcp: {
                    "tools": {
                        "name": "tools",
                        "type": "mcp",
                        "auth": {"type": "none"},
                        "base_url": "https://mcp.test.com",
                        "timeout": 5,
                        "refresh": {"interval": "120", "retry_delay": "2", "max_retry_delay": "30"},
                    }
                }
            }
        }
    )

    connector = MapperDomainSchema.map(schema).connector.mcp("tools")

    assert connector.refresh == McpRefresh(interval=120, retry_delay=2, max_retry_delay=30)


def test_mcp_connector_refuses_a_refresh_that_cannot_schedule():
    with pytest.raises(ValidationError, match="max_retry_delay"):
        ApplicationConfigurationSchema(
            **REQUIRED
            | {
                "connector": {
                    ConnectorType.mcp: {
                        "tools": {
                            "name": "tools",
                            "type": "mcp",
                            "auth": {"type": "none"},
                            "base_url": "https://mcp.test.com",
                            "timeout": 5,
                            "refresh": {"retry_delay": 10, "max_retry_delay": 5},
                        }
                    }
                }
            }
        )


@pytest.mark.parametrize("missing", ["log", "server"])
def test_log_and_server_are_required(missing):
    with pytest.raises(ValidationError, match=missing):
        ApplicationConfigurationSchema(
            **{name: value for name, value in REQUIRED.items() if name != missing}
        )


def test_a_server_dict_resolves_to_a_typed_asgi_server():
    schema = ApplicationConfigurationSchema(
        **REQUIRED
        | {
            "log": "DEBUG",
            "server": {
                ServerType.asgi: {
                    "orders-api": {
                        "name": "orders-api",
                        "type": "asgi",
                        "base_path": "/orders-api",
                        "docs": "true",
                        "cors_origins": ["https://shop.example.com"],
                        "parameters": {"max_open_orders": "50"},
                    }
                }
            },
        }
    )

    result = MapperDomainSchema.map(schema)
    server = result.server.asgi("orders-api")

    assert result.log is LogLevel.DEBUG
    assert isinstance(server, AsgiServer)
    assert server.base_path == "/orders-api"
    assert server.docs is True
    assert server.cors_origins == ["https://shop.example.com"]
    assert server.parameters == {"max_open_orders": "50"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("log", "VERBOSE"),
        ("server", {"asgi": {"x": {"name": "x", "type": "asgi", "docs": "maybe"}}}),
    ],
)
def test_an_unknown_log_level_or_an_invalid_server_is_rejected(field, value):
    with pytest.raises(ValidationError):
        ApplicationConfigurationSchema(**REQUIRED | {field: value})


DATABASE_CONNECTOR = {
    "name": "pg",
    "type": "database",
    "engine": "postgresql",
    "host": "db",
    "port": 5432,
    "timeout": 3,
    "pool": {"min": 1, "max": 5},
    "auth": {"type": "none"},
}


def test_a_database_operation_carries_its_connector_and_what_it_works_on():
    schema = ApplicationConfigurationSchema(
        **REQUIRED
        | {
            "connector": {ConnectorType.database: {"pg": DATABASE_CONNECTOR}},
            "operation": {
                "orders": {
                    "name": "orders",
                    "type": "database",
                    "connector": DATABASE_CONNECTOR,
                    "database": "shop",
                    "collections": {"orders": "orders"},
                    "ttl": 3600,
                }
            },
        }
    )

    configuration = MapperDomainSchema.map(schema)
    orders = configuration.operation.database("orders")

    assert orders.connector == configuration.connector.database("pg")
    assert (orders.database, orders.collection("orders"), orders.ttl) == ("shop", "orders", 3600)
    assert orders.connector.pool.max == 5


@pytest.mark.parametrize(
    ("connector", "field"),
    [
        (DATABASE_CONNECTOR | {"default_name": "shop"}, "default_name"),
        (DATABASE_CONNECTOR | {"pool": {"max": 5, "ttl": 604800}}, "pool.ttl"),
        (DATABASE_CONNECTOR | {"pool": {"timeout_ms": 3000}}, "pool.timeout_ms"),
    ],
)
def test_a_5x_database_connector_is_refused_and_names_the_key_to_move(connector, field):
    with pytest.raises(ValidationError, match=field.replace(".", r"\.")):
        ApplicationConfigurationSchema(
            **REQUIRED | {"connector": {ConnectorType.database: {"pg": connector}}}
        )


def test_an_a2a_connector_and_operation_resolve_by_their_type():
    agent = {
        "name": "agent",
        "type": "a2a",
        "base_url": "http://agent:8000/a2a",
        "timeout": 60,
        "auth": {"type": "none"},
    }
    schema = ApplicationConfigurationSchema(
        **REQUIRED
        | {
            "connector": {ConnectorType.a2a: {"agent": agent}},
            "operation": {
                "ask": {"name": "ask", "type": "a2a", "connector": agent, "parameters": {"k": "v"}}
            },
        }
    )

    configuration = MapperDomainSchema.map(schema)

    assert configuration.connector.a2a("agent").binding == "JSONRPC"
    assert configuration.operation.a2a("ask").parameters == {"k": "v"}
