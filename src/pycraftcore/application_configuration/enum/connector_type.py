from enum import Enum


class ConnectorType(Enum):
    api = "api"
    database = "database"
    cache = "cache"
    file = "file"
    telemetry = "telemetry"
    mcp = "mcp"
    a2a = "a2a"
