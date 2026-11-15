from pycraftcore.repository.adapter.sql.postgresql.schema import PostgresConnector
from pycraftcore.repository.adapter.sql.sqlalchemy import postgresql_engine_builder
from pycraftcore.repository.adapter.sql.sqlalchemy.postgresql_engine_builder import (
    PostgresEngineBuilder,
)


def make_settings(**overrides) -> PostgresConnector:
    defaults = dict(
        host="db.internal",
        port=5432,
        database="app",
        user="alice",
        password="p@ss/word",
        connect_timeout=5,
        min_pool_size=1,
        max_pool_size=3,
    )
    defaults.update(overrides)
    return PostgresConnector(**defaults)


def test_the_engine_points_at_the_connector_database_through_psycopg():
    url = PostgresEngineBuilder(make_settings()).build().url

    assert url.drivername == "postgresql+psycopg"
    assert (url.host, url.port, url.database) == ("db.internal", 5432, "app")
    assert (url.username, url.password) == ("alice", "p@ss/word")


def test_a_password_with_reserved_characters_is_escaped_in_the_url():
    url = PostgresEngineBuilder(make_settings()).build().url

    assert "p%40ss%2Fword" in url.render_as_string(hide_password=False)


def test_the_pool_holds_at_most_max_pool_size_connections():
    pool = PostgresEngineBuilder(make_settings(max_pool_size=5)).build().pool

    assert pool.size() == 5
    assert pool._max_overflow == 0
    assert pool._pre_ping is True


def test_queries_use_the_same_placeholders_as_postgres_repository():
    engine = PostgresEngineBuilder(make_settings()).build()

    assert engine.dialect.paramstyle == "pyformat"


def test_building_does_not_connect():
    engine = PostgresEngineBuilder(make_settings(host="unreachable.invalid")).build()

    assert engine.pool.checkedout() == 0


def test_connecting_gives_up_after_the_connect_timeout(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(
        postgresql_engine_builder,
        "create_async_engine",
        lambda url, **options: calls.append(options),
    )

    PostgresEngineBuilder(make_settings(connect_timeout=7)).build()

    assert calls[0]["connect_args"] == {"connect_timeout": 7}
