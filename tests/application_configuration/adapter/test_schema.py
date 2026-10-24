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
from pycraftcore.application_configuration.model.connector import McpConnector
from pycraftcore.application_configuration.model.server import AsgiServer
from pycraftcore.logger.enum.log_level import LogLevel
from pycraftcore.web.enum.web_framework import WebFramework


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
                        "framework": "litestar",
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
    assert server.framework is WebFramework.LITESTAR
    assert server.base_path == "/orders-api"
    assert server.docs is True
    assert server.cors_origins == ["https://shop.example.com"]
    assert server.parameters == {"max_open_orders": "50"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("log", "VERBOSE"),
        ("server", {"asgi": {"x": {"name": "x", "type": "asgi", "framework": "flask"}}}),
    ],
)
def test_an_unknown_log_level_or_framework_is_rejected(field, value):
    with pytest.raises(ValidationError):
        ApplicationConfigurationSchema(**REQUIRED | {field: value})
