from unittest.mock import MagicMock

from pycraftcore.repository.port.repository import AsyncRepository, AsyncRepositoryFactory
from pycraftcore.repository.adapter.sql.postgresql.adapter import PostgresRepository
from pycraftcore.repository.adapter.sql.postgresql.factory import PostgresRepositoryFactory
from pycraftcore.repository.adapter.sql.postgresql.schema import PostgresConnector


def test_postgres_repository_satisfies_async_repository():
    repository: AsyncRepository = PostgresRepository(MagicMock())

    assert isinstance(repository, AsyncRepository)


def test_postgres_repository_factory_satisfies_async_repository_factory():
    settings = PostgresConnector(
        host="localhost",
        port=5432,
        default_name="main",
        user=None,
        password=None,
        min_pool_size=1,
        max_pool_size=1,
    )
    factory: AsyncRepositoryFactory = PostgresRepositoryFactory(settings)

    assert isinstance(factory, AsyncRepositoryFactory)
