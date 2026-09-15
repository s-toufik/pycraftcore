from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model.connector import DatabaseConnector
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.basic_auth import BasicAuth
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.repository.adapter.sql.postgresql.mapper import PostgresSettingsMapper


def make_connector(auth, pool: dict) -> DatabaseConnector:
    return DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=auth,
        engine="postgresql",
        host="db.internal",
        port=5432,
        default_name="app",
        pool=pool,
    )


def test_maps_host_port_and_default_name():
    connector = make_connector(NoAuth(type=AuthType.none), pool={})
    mapper = PostgresSettingsMapper(connector)

    settings = mapper()

    assert settings.host == "db.internal"
    assert settings.port == 5432
    assert settings.default_name == "app"


def test_maps_basic_auth_credentials():
    connector = make_connector(
        BasicAuth(username="alice", password="secret", type=AuthType.basic), pool={}
    )
    mapper = PostgresSettingsMapper(connector)

    settings = mapper()

    assert settings.user == "alice"
    assert settings.password == "secret"


def test_defaults_credentials_to_none_when_auth_has_no_username_or_password():
    connector = make_connector(NoAuth(type=AuthType.none), pool={})
    mapper = PostgresSettingsMapper(connector)

    settings = mapper()

    assert settings.user is None
    assert settings.password is None


def test_maps_pool_min_and_max_to_pool_sizes():
    connector = make_connector(NoAuth(type=AuthType.none), pool={"min": 2, "max": 8})
    mapper = PostgresSettingsMapper(connector)

    settings = mapper()

    assert settings.min_pool_size == 2
    assert settings.max_pool_size == 8


def test_defaults_pool_sizes_to_one_when_missing():
    connector = make_connector(NoAuth(type=AuthType.none), pool={})
    mapper = PostgresSettingsMapper(connector)

    settings = mapper()

    assert settings.min_pool_size == 1
    assert settings.max_pool_size == 1
