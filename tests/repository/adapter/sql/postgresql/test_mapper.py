from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model import (
    DatabaseConnector,
    DatabaseOperation,
    DatabasePool,
)
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.basic_auth import BasicAuth
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.repository.adapter.sql.postgresql.mapper import PostgresSettingsMapper


def make_operation(
    auth=None, pool: DatabasePool | None = None, timeout: int = 5
) -> DatabaseOperation:
    connector = DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=auth or NoAuth(type=AuthType.none),
        engine="postgresql",
        host="db.internal",
        port=5432,
        timeout=timeout,
        pool=pool or DatabasePool(),
    )
    return DatabaseOperation(
        name="orders", type=OperationType.database, connector=connector, database="app"
    )


def test_the_connection_comes_from_the_connector_and_the_database_from_the_operation():
    settings = PostgresSettingsMapper(make_operation())()

    assert (settings.host, settings.port, settings.database) == ("db.internal", 5432, "app")


def test_maps_basic_auth_credentials():
    auth = BasicAuth(username="alice", password="secret", type=AuthType.basic)

    settings = PostgresSettingsMapper(make_operation(auth))()

    assert (settings.user, settings.password) == ("alice", "secret")


def test_defaults_credentials_to_none_when_auth_has_no_username_or_password():
    settings = PostgresSettingsMapper(make_operation())()

    assert (settings.user, settings.password) == (None, None)


def test_maps_the_pool_to_pool_sizes():
    settings = PostgresSettingsMapper(make_operation(pool=DatabasePool(min=2, max=8)))()

    assert (settings.min_pool_size, settings.max_pool_size) == (2, 8)


def test_the_default_pool_is_one_connection():
    settings = PostgresSettingsMapper(make_operation())()

    assert (settings.min_pool_size, settings.max_pool_size) == (1, 1)


def test_the_connector_timeout_is_the_connect_timeout():
    settings = PostgresSettingsMapper(make_operation(timeout=3))()

    assert settings.connect_timeout == 3
