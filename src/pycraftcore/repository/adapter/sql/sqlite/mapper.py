from pycraftcore.application_configuration.model import DatabaseOperation
from pycraftcore.repository.adapter.sql.sqlite.schema import SqliteConnector


class SqliteSettingsMapper:
    def __init__(self, operation: DatabaseOperation) -> None:
        self._operation = operation

    def __call__(self) -> SqliteConnector:
        connector = self._operation.connector
        return SqliteConnector(
            path=connector.host,
            database=self._operation.database,
            max_pool_size=connector.pool.max,
        )
