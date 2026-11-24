from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model import (
    DatabaseConnector,
    DatabaseOperation,
    DatabasePool,
)
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.repository.adapter.sql.sqlite import SqliteSettingsMapper


def make_operation(pool: DatabasePool | None = None) -> DatabaseOperation:
    connector = DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=NoAuth(type=AuthType.none),
        engine="sqlite",
        host="/var/data",
        port=0,
        pool=pool or DatabasePool(),
    )
    return DatabaseOperation(
        name="users", type=OperationType.database, connector=connector, database="main"
    )


def test_the_folder_comes_from_the_connector_and_the_file_from_the_operation():
    settings = SqliteSettingsMapper(make_operation())()

    assert (settings.path, settings.database) == ("/var/data", "main")


def test_maps_pool_max_to_max_pool_size():
    settings = SqliteSettingsMapper(make_operation(DatabasePool(max=4)))()

    assert settings.max_pool_size == 4


def test_the_default_pool_is_one_connection():
    assert SqliteSettingsMapper(make_operation())().max_pool_size == 1
