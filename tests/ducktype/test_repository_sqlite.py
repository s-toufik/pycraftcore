from unittest.mock import MagicMock

from pycraftcore.repository.port.repository import AsyncRepository, AsyncRepositoryFactory
from pycraftcore.repository.adapter.sqlite.adapter import SqliteRepository
from pycraftcore.repository.adapter.sqlite.factory import SQLiteRepositoryFactory
from pycraftcore.repository.adapter.sqlite import SqliteConnector


def test_sqlite_repository_satisfies_async_repository():
    repository: AsyncRepository = SqliteRepository([MagicMock()])

    assert isinstance(repository, AsyncRepository)


def test_sqlite_repository_factory_satisfies_async_repository_factory(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main", max_pool_size=1)
    factory: AsyncRepositoryFactory = SQLiteRepositoryFactory(settings)

    assert isinstance(factory, AsyncRepositoryFactory)
