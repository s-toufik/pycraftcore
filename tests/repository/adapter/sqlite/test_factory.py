from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pycraftcore.repository.adapter.sqlite.factory import SQLiteRepositoryFactory
from pycraftcore.repository.adapter.sqlite import SqliteConnector


def make_fake_client() -> MagicMock:
    client = MagicMock()
    client.execute = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_connection_creates_directory_and_memoizes_client(tmp_path):
    db_dir = tmp_path / "data"
    settings = SqliteConnector(path=str(db_dir), default_name="main", max_pool_size=1)
    factory = SQLiteRepositoryFactory(settings)
    fake_client = make_fake_client()

    with patch(
        "pycraftcore.repository.adapter.sqlite.factory.connect",
        AsyncMock(return_value=fake_client),
    ) as mock_connect:
        first = await factory.connection()
        second = await factory.connection()

    assert db_dir.exists()
    assert first is fake_client
    assert second is fake_client
    mock_connect.assert_awaited_once()
    assert mock_connect.call_args[0][0] == str(db_dir / "main.db")


@pytest.mark.asyncio
async def test_connection_applies_wal_and_busy_timeout_pragmas(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main", max_pool_size=1)
    factory = SQLiteRepositoryFactory(settings)
    fake_client = make_fake_client()

    with patch(
        "pycraftcore.repository.adapter.sqlite.factory.connect",
        AsyncMock(return_value=fake_client),
    ):
        await factory.connection()

    executed_pragmas = [call.args[0] for call in fake_client.execute.call_args_list]
    assert "PRAGMA journal_mode=WAL" in executed_pragmas
    assert "PRAGMA busy_timeout=5000" in executed_pragmas
    assert "PRAGMA synchronous=NORMAL" in executed_pragmas


@pytest.mark.asyncio
async def test_connection_does_not_create_directory_when_it_already_exists(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main", max_pool_size=1)
    factory = SQLiteRepositoryFactory(settings)

    with patch(
        "pycraftcore.repository.adapter.sqlite.factory.connect",
        AsyncMock(return_value=make_fake_client()),
    ):
        await factory.connection()

    assert tmp_path.exists()


@pytest.mark.asyncio
async def test_connect_returns_repository_backed_by_a_connection_pool(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main", max_pool_size=3)
    factory = SQLiteRepositoryFactory(settings)

    with patch(
        "pycraftcore.repository.adapter.sqlite.factory.connect",
        AsyncMock(side_effect=lambda *_args, **_kwargs: make_fake_client()),
    ) as mock_connect:
        repository = await factory.connect()
        second_repository = await factory.connect()

    assert mock_connect.await_count == 3
    assert repository._pool.qsize() == 3
    assert second_repository is repository


@pytest.mark.asyncio
async def test_connect_and_connection_use_independent_underlying_resources(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main", max_pool_size=2)
    factory = SQLiteRepositoryFactory(settings)

    with patch(
        "pycraftcore.repository.adapter.sqlite.factory.connect",
        AsyncMock(side_effect=lambda *_args, **_kwargs: make_fake_client()),
    ) as mock_connect:
        connection = await factory.connection()
        repository = await factory.connect()

    assert mock_connect.await_count == 3
    assert connection is not None
    assert repository is not None


@pytest.mark.asyncio
async def test_disconnect_closes_client_and_pool_and_is_idempotent(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main", max_pool_size=2)
    factory = SQLiteRepositoryFactory(settings)
    clients = [make_fake_client(), make_fake_client(), make_fake_client()]

    with patch(
        "pycraftcore.repository.adapter.sqlite.factory.connect",
        AsyncMock(side_effect=clients),
    ):
        await factory.connection()
        await factory.connect()

    await factory.disconnect()
    for client in clients:
        client.close.assert_awaited_once()

    await factory.disconnect()
    for client in clients:
        client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_without_prior_connection_is_a_no_op(tmp_path):
    settings = SqliteConnector(path=str(tmp_path), default_name="main", max_pool_size=1)
    factory = SQLiteRepositoryFactory(settings)

    await factory.disconnect()
