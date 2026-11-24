from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model import (
    A2aConnector,
    ApiConnector,
    DatabaseConnector,
    FileConnector,
    McpConnector,
)
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.no_auth import NoAuth

NO_AUTH = NoAuth(type=AuthType.none)


def api_connector() -> ApiConnector:
    return ApiConnector(
        name="llm",
        type=ConnectorType.api,
        auth=NO_AUTH,
        base_url="https://api.test.com",
        timeout=30,
        retry=3,
    )


def file_connector() -> FileConnector:
    return FileConnector(
        name="files", type=ConnectorType.file, auth=NO_AUTH, base_path="/var/files"
    )


def database_connector(**overrides) -> DatabaseConnector:
    values = dict(
        name="db",
        type=ConnectorType.database,
        auth=NO_AUTH,
        engine="sqlite",
        host="/var/data",
        port=0,
    )
    values.update(overrides)
    return DatabaseConnector(**values)


def mcp_connector(**overrides) -> McpConnector:
    values = dict(
        name="tools",
        type=ConnectorType.mcp,
        auth=NO_AUTH,
        base_url="https://mcp.test.com",
        timeout=5,
    )
    values.update(overrides)
    return McpConnector(**values)


def a2a_connector() -> A2aConnector:
    return A2aConnector(
        name="agent",
        type=ConnectorType.a2a,
        auth=NO_AUTH,
        base_url="http://agent:8000/a2a",
        timeout=60,
    )
