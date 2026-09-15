from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pycraftcore.repository.adapter.sql.postgresql.adapter import PostgresRepository
from pycraftcore.repository.adapter.sql.postgresql.factory import PostgresRepositoryFactory
from pycraftcore.repository.adapter.sql.postgresql.schema import PostgresConnector


def make_settings(**overrides) -> PostgresConnector:
    defaults = dict(
        host="localhost",
        port=5432,
        default_name="main",
        user="user",
        password="secret",
        min_pool_size=1,
        max_pool_size=3,
    )
    defaults.update(overrides)
    return PostgresConnector(**defaults)


def make_fake_client() -> AsyncMock:
    client = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_connection_opens_and_memoizes_client():
    factory = PostgresRepositoryFactory(make_settings())
    fake_client = make_fake_client()

    with patch(
        "pycraftcore.repository.adapter.sql.postgresql.factory.AsyncConnection"
    ) as mock_connection_cls:
        mock_connection_cls.connect = AsyncMock(return_value=fake_client)

        first = await factory.connection()
        second = await factory.connection()

    assert first is fake_client
    assert second is fake_client
    mock_connection_cls.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_connection_builds_conninfo_from_settings():
    factory = PostgresRepositoryFactory(
        make_settings(host="db.internal", port=6543, default_name="app", user="alice", password="pw")
    )

    with patch(
        "pycraftcore.repository.adapter.sql.postgresql.factory.AsyncConnection"
    ) as mock_connection_cls:
        mock_connection_cls.connect = AsyncMock(return_value=make_fake_client())

        await factory.connection()

    conninfo = mock_connection_cls.connect.call_args[0][0]
    assert "host=db.internal" in conninfo
    assert "port=6543" in conninfo
    assert "dbname=app" in conninfo
    assert "user=alice" in conninfo


@pytest.mark.asyncio
async def test_connect_returns_repository_backed_by_an_opened_pool():
    factory = PostgresRepositoryFactory(make_settings(min_pool_size=1, max_pool_size=3))

    with patch(
        "pycraftcore.repository.adapter.sql.postgresql.factory.AsyncConnectionPool"
    ) as mock_pool_cls:
        fake_pool = MagicMock()
        fake_pool.open = AsyncMock()
        fake_pool.close = AsyncMock()
        mock_pool_cls.return_value = fake_pool

        repository = await factory.connect()
        second_repository = await factory.connect()

    mock_pool_cls.assert_called_once()
    _, kwargs = mock_pool_cls.call_args
    assert kwargs["min_size"] == 1
    assert kwargs["max_size"] == 3
    assert kwargs["open"] is False
    fake_pool.open.assert_awaited_once_with(wait=True)
    assert isinstance(repository, PostgresRepository)
    assert second_repository is repository


@pytest.mark.asyncio
async def test_disconnect_closes_client_and_pool_and_is_idempotent():
    factory = PostgresRepositoryFactory(make_settings())
    fake_client = make_fake_client()
    fake_pool = MagicMock()
    fake_pool.open = AsyncMock()
    fake_pool.close = AsyncMock()

    with (
        patch(
            "pycraftcore.repository.adapter.sql.postgresql.factory.AsyncConnection"
        ) as mock_connection_cls,
        patch(
            "pycraftcore.repository.adapter.sql.postgresql.factory.AsyncConnectionPool",
            return_value=fake_pool,
        ),
    ):
        mock_connection_cls.connect = AsyncMock(return_value=fake_client)
        await factory.connection()
        await factory.connect()

    await factory.disconnect()
    fake_client.close.assert_awaited_once()
    fake_pool.close.assert_awaited_once()

    await factory.disconnect()
    fake_client.close.assert_awaited_once()
    fake_pool.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_without_prior_connection_is_a_no_op():
    factory = PostgresRepositoryFactory(make_settings())

    await factory.disconnect()
