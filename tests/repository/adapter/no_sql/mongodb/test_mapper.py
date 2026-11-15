from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model.connector import DatabaseConnector
from pycraftcore.application_configuration.model.operation import DatabaseOperation
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.basic_auth import BasicAuth
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.repository.adapter.no_sql.mongodb.mapper import MongoSettingsMapper


def make_operation(auth=None, timeout: int = 5) -> DatabaseOperation:
    connector = DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=auth or NoAuth(type=AuthType.none),
        engine="mongodb",
        host="db.internal",
        port=27017,
        timeout=timeout,
    )
    return DatabaseOperation(
        name="events", type=OperationType.database, connector=connector, database="app"
    )


def test_the_connection_comes_from_the_connector_and_the_database_from_the_operation():
    settings = MongoSettingsMapper(make_operation())()

    assert (settings.host, settings.port, settings.database) == ("db.internal", 27017, "app")


def test_maps_basic_auth_credentials():
    auth = BasicAuth(username="alice", password="secret", type=AuthType.basic)

    settings = MongoSettingsMapper(make_operation(auth))()

    assert (settings.username, settings.password) == ("alice", "secret")


def test_defaults_credentials_to_none_when_auth_has_no_username_or_password():
    settings = MongoSettingsMapper(make_operation())()

    assert (settings.username, settings.password) == (None, None)


def test_the_connector_timeout_in_seconds_is_the_server_selection_timeout_in_ms():
    settings = MongoSettingsMapper(make_operation(timeout=3))()

    assert settings.server_selection_timeout_ms == 3000
