from unittest.mock import MagicMock

from pycraftcore.repository.port.repository import AsyncRepository, AsyncRepositoryFactory
from pycraftcore.repository.adapter.no_sql.mongodb.adapter import MongoRepository
from pycraftcore.repository.adapter.no_sql.mongodb.factory import MongoRepositoryFactory
from pycraftcore.repository.adapter.no_sql.mongodb.schema import MongoConnector


def test_mongo_repository_satisfies_async_repository():
    repository: AsyncRepository = MongoRepository(MagicMock(), "app")

    assert isinstance(repository, AsyncRepository)


def test_mongo_repository_factory_satisfies_async_repository_factory():
    settings = MongoConnector(
        host="localhost",
        port=27017,
        default_name="main",
        username=None,
        password=None,
        server_selection_timeout_ms=5000,
    )
    factory: AsyncRepositoryFactory = MongoRepositoryFactory(settings)

    assert isinstance(factory, AsyncRepositoryFactory)
