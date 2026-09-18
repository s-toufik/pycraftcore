from unittest.mock import MagicMock, patch

import pytest

from pycraftcore.repository.adapter.no_sql.mongodb.adapter import MongoRepository
from pycraftcore.repository.adapter.no_sql.mongodb.factory import MongoRepositoryFactory
from pycraftcore.repository.adapter.no_sql.mongodb.schema import MongoConnector


def make_settings(**overrides) -> MongoConnector:
    defaults = dict(
        host="localhost",
        port=27017,
        default_name="app",
        username=None,
        password=None,
        server_sellection_timeout=5000,
    )
    defaults.update(overrides)
    return MongoConnector(**defaults)


@pytest.mark.asyncio
async def test_connection_opens_and_memoizes_client():
    factory = MongoRepositoryFactory(make_settings())
    fake_client = MagicMock()

    with patch(
        "pycraftcore.repository.adapter.no_sql.mongodb.factory.MongoClient",
        return_value=fake_client,
    ) as mock_client_cls:
        first = await factory.connection()
        second = await factory.connection()

    assert first is fake_client
    assert second is fake_client
    mock_client_cls.assert_called_once()


@pytest.mark.asyncio
async def test_connection_uri_omits_credentials_when_not_configured():
    factory = MongoRepositoryFactory(make_settings(host="db.internal", port=27018))

    with patch(
        "pycraftcore.repository.adapter.no_sql.mongodb.factory.MongoClient"
    ) as mock_client_cls:
        await factory.connection()

    mock_client_cls.assert_called_once_with(
        "mongodb://db.internal:27018", serverSelectionTimeoutMS=5000
    )


@pytest.mark.asyncio
async def test_connection_uri_includes_credentials_when_configured():
    factory = MongoRepositoryFactory(
        make_settings(host="db.internal", port=27018, username="alice", password="secret")
    )

    with patch(
        "pycraftcore.repository.adapter.no_sql.mongodb.factory.MongoClient"
    ) as mock_client_cls:
        await factory.connection()

    mock_client_cls.assert_called_once_with(
        "mongodb://alice:secret@db.internal:27018/?authSource=admin",
        serverSelectionTimeoutMS=5000,
    )


@pytest.mark.asyncio
async def test_connect_returns_repository_wrapping_the_client():
    factory = MongoRepositoryFactory(make_settings(default_name="app"))

    with patch(
        "pycraftcore.repository.adapter.no_sql.mongodb.factory.MongoClient"
    ) as mock_client_cls:
        mock_client_cls.return_value = MagicMock()

        repository = await factory.connect()
        second_repository = await factory.connect()

    assert isinstance(repository, MongoRepository)
    assert second_repository is repository
    mock_client_cls.assert_called_once()


@pytest.mark.asyncio
async def test_ping_reuses_existing_connection():
    factory = MongoRepositoryFactory(make_settings())
    fake_client = MagicMock()

    with patch(
        "pycraftcore.repository.adapter.no_sql.mongodb.factory.MongoClient",
        return_value=fake_client,
    ):
        await factory.connection()
        await factory.ping()

    fake_client.admin.command.assert_called_once_with("ping")


@pytest.mark.asyncio
async def test_disconnect_closes_client_and_resets_state():
    factory = MongoRepositoryFactory(make_settings())
    fake_client = MagicMock()

    with patch(
        "pycraftcore.repository.adapter.no_sql.mongodb.factory.MongoClient",
        return_value=fake_client,
    ):
        await factory.connect()

    await factory.disconnect()

    fake_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect_without_prior_connection_is_a_no_op():
    factory = MongoRepositoryFactory(make_settings())

    await factory.disconnect()
