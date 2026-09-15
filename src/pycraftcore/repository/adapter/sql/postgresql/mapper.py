from pycraftcore.application_configuration.model.connector import DatabaseConnector
from pycraftcore.repository.adapter.sql.postgresql.schema import PostgresConnector


class PostgresSettingsMapper:
    def __init__(self, database_connector: DatabaseConnector) -> None:
        self._database_connector = database_connector

    def __call__(self) -> PostgresConnector:

        return PostgresConnector(
            host=self._database_connector.host,
            port=self._database_connector.port,
            default_name=self._database_connector.default_name,
            user=getattr(self._database_connector.auth, "username", None),
            password=getattr(self._database_connector.auth, "password", None),
            min_pool_size=self._database_connector.pool.get("min", 1),
            max_pool_size=self._database_connector.pool.get("max", 1),
        )
