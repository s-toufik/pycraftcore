from enum import Enum


class ConnectorType(Enum):
    api = "api"
    database = "database"
    cache = "cache"
    file = "file"
    telemetry = "telemetry"
