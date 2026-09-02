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
from pycraftcore.application_configuration.model.connector import McpConnector


def test_map_converts_schema_into_domain_model():
    schema = ApplicationConfigurationSchema(
        env=RunTypeEnvironment.debug,
        run=RunTypeApplication.asynchronous,
        connector={},
        operation={},
    )

    result = MapperDomainSchema.map(schema)

    assert isinstance(result, ApplicationConfiguration)
    assert result.env == RunTypeEnvironment.debug
    assert result.run == RunTypeApplication.asynchronous
    assert result.connector.by_type == {}
    assert result.operation.by_name == {}


def test_mcp_connector_dict_resolves_to_mcp_connector_via_the_type_discriminator():
    schema = ApplicationConfigurationSchema(
        env=RunTypeEnvironment.debug,
        run=RunTypeApplication.asynchronous,
        connector={
            ConnectorType.mcp: {
                "tools": {
                    "name": "tools",
                    "type": "mcp",
                    "auth": {"type": "none"},
                    "base_url": "https://mcp.test.com",
                    "timeout": 5,
                }
            }
        },
        operation={},
    )

    result = MapperDomainSchema.map(schema)
    connector = result.connector.mcp("tools")

    assert isinstance(connector, McpConnector)
    assert connector.base_url == "https://mcp.test.com"
    assert connector.transport == "streamable_http"
