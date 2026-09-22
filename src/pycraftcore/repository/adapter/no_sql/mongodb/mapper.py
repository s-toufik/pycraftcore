from pycraftcore.application_configuration.model.connector import DatabaseConnector
from pycraftcore.repository.adapter.no_sql.mongodb.schema import MongoConnector


class MongoSettingsMapper:
    def __init__(self, database_connector: DatabaseConnector) -> None:
        self._database_connector = database_connector

    def __call__(self) -> MongoConnector:
        auth = self._database_connector.auth

        return MongoConnector(
            host=self._database_connector.host,
            port=self._database_connector.port,
            default_name=self._database_connector.default_name,
            username=getattr(auth, "username", None),
            password=getattr(auth, "password", None),
            server_selection_timeout_ms=self._database_connector.pool.get("timeout_ms", 5000),
        )
