from pycraftcore.application_configuration.model.operation import DatabaseOperation
from pycraftcore.repository.adapter.no_sql.mongodb.schema import MongoConnector

MILLISECONDS_PER_SECOND: int = 1000


class MongoSettingsMapper:
    def __init__(self, operation: DatabaseOperation) -> None:
        self._operation = operation

    def __call__(self) -> MongoConnector:
        connector = self._operation.connector
        auth = connector.auth

        return MongoConnector(
            host=connector.host,
            port=connector.port,
            database=self._operation.database,
            username=getattr(auth, "username", None),
            password=getattr(auth, "password", None),
            server_selection_timeout_ms=connector.timeout * MILLISECONDS_PER_SECOND,
        )
