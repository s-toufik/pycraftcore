from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model.connector import DatabaseConnector
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.basic_auth import BasicAuth
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.repository.adapter.no_sql.mongodb.mapper import MongoSettingsMapper


def make_connector(auth, pool: dict) -> DatabaseConnector:
    return DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=auth,
        engine="mongodb",
        host="db.internal",
        port=27017,
        default_name="app",
        pool=pool,
    )


def test_maps_host_port_and_default_name():
    connector = make_connector(NoAuth(type=AuthType.none), pool={})
    mapper = MongoSettingsMapper(connector)

    settings = mapper()

    assert settings.host == "db.internal"
    assert settings.port == 27017
    assert settings.default_name == "app"


def test_maps_basic_auth_credentials():
    connector = make_connector(
        BasicAuth(username="alice", password="secret", type=AuthType.basic), pool={}
    )
    mapper = MongoSettingsMapper(connector)

    settings = mapper()

    assert settings.username == "alice"
    assert settings.password == "secret"


def test_defaults_credentials_to_none_when_auth_has_no_username_or_password():
    connector = make_connector(NoAuth(type=AuthType.none), pool={})
    mapper = MongoSettingsMapper(connector)

    settings = mapper()

    assert settings.username is None
    assert settings.password is None


def test_maps_pool_timeout_ms_to_server_sellection_timeout():
    connector = make_connector(NoAuth(type=AuthType.none), pool={"timeout_ms": 10000})
    mapper = MongoSettingsMapper(connector)

    settings = mapper()

    assert settings.server_sellection_timeout == 10000


def test_defaults_server_sellection_timeout_when_missing():
    connector = make_connector(NoAuth(type=AuthType.none), pool={})
    mapper = MongoSettingsMapper(connector)

    settings = mapper()

    assert settings.server_sellection_timeout == 5000
