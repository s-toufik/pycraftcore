from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model.connector import DatabaseConnector
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.repository.sqlite.mapper import SqliteSettingsMapper


def make_connector(pool: dict) -> DatabaseConnector:
    return DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=NoAuth(type=AuthType.none),
        engine="sqlite",
        host="/var/data",
        port=0,
        default_name="main",
        pool=pool,
    )


def test_maps_host_to_path_and_default_name():
    mapper = SqliteSettingsMapper(make_connector(pool={}))

    settings = mapper()

    assert settings.path == "/var/data"
    assert settings.default_name == "main"


def test_maps_pool_max_to_max_pool_size():
    mapper = SqliteSettingsMapper(make_connector(pool={"max": 4}))

    settings = mapper()

    assert settings.max_pool_size == 4


def test_defaults_max_pool_size_to_one_when_missing():
    mapper = SqliteSettingsMapper(make_connector(pool={}))

    settings = mapper()

    assert settings.max_pool_size == 1
