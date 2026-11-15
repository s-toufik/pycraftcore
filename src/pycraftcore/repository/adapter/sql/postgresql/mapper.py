from pycraftcore.application_configuration.model.operation import DatabaseOperation
from pycraftcore.repository.adapter.sql.postgresql.schema import PostgresConnector


class PostgresSettingsMapper:
    def __init__(self, operation: DatabaseOperation) -> None:
        self._operation = operation

    def __call__(self) -> PostgresConnector:
        connector = self._operation.connector
        return PostgresConnector(
            host=connector.host,
            port=connector.port,
            database=self._operation.database,
            user=getattr(connector.auth, "username", None),
            password=getattr(connector.auth, "password", None),
            connect_timeout=connector.timeout,
            min_pool_size=connector.pool.min,
            max_pool_size=connector.pool.max,
        )
