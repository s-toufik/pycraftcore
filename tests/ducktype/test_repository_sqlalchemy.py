from unittest.mock import MagicMock

from pycraftcore.repository.adapter.sql.postgresql.schema import PostgresConnector
from pycraftcore.repository.adapter.sql.sqlalchemy import (
    PostgresEngineBuilder,
    SqlAlchemyEngineBuilder,
    SqlAlchemyRepository,
    SqlAlchemyRepositoryFactory,
    SqliteEngineBuilder,
)
from pycraftcore.repository.adapter.sql.sqlite import SqliteConnector
from pycraftcore.repository.port.repository import AsyncRepository, AsyncRepositoryFactory


def test_sqlalchemy_repository_satisfies_async_repository():
    repository: AsyncRepository = SqlAlchemyRepository(MagicMock())

    assert isinstance(repository, AsyncRepository)


def test_sqlalchemy_repository_factory_satisfies_async_repository_factory():
    factory: AsyncRepositoryFactory = SqlAlchemyRepositoryFactory(MagicMock())

    assert isinstance(factory, AsyncRepositoryFactory)


def test_both_engine_builders_satisfy_the_engine_builder_port(tmp_path):
    postgres = PostgresConnector(
        host="localhost",
        port=5432,
        database="main",
        user=None,
        password=None,
        connect_timeout=5,
        min_pool_size=1,
        max_pool_size=1,
    )
    sqlite = SqliteConnector(path=str(tmp_path), database="main", max_pool_size=1)
    builders: list[SqlAlchemyEngineBuilder] = [
        PostgresEngineBuilder(postgres),
        SqliteEngineBuilder(sqlite),
    ]

    assert all(isinstance(builder, SqlAlchemyEngineBuilder) for builder in builders)
