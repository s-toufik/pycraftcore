import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pycraftcore.repository.sqlite.adapter import SqliteRepository


@pytest.fixture
def fake_cursor():
    cursor = MagicMock()

    cursor.description = ["id", "name"]

    cursor.fetchall = AsyncMock(
        return_value=[
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Alice"},
        ]
    )

    return cursor


@pytest.fixture
def fake_connection(fake_cursor):
    connection = MagicMock()

    connection.execute = AsyncMock(return_value=fake_cursor)

    return connection


@pytest.fixture
def repository(fake_connection):
    return SqliteRepository([fake_connection])


@pytest.mark.asyncio
async def test_execute_returns_rows_as_dict(
    repository,
    fake_connection,
):
    result = await repository.execute("SELECT * FROM users")

    fake_connection.execute.assert_called_once_with("SELECT * FROM users", ())

    assert result == [
        {"id": 1, "name": "John"},
        {"id": 2, "name": "Alice"},
    ]


@pytest.mark.asyncio
async def test_execute_commits_and_returns_empty_list_when_no_result_set():
    cursor = MagicMock()
    cursor.description = None
    connection = MagicMock()
    connection.execute = AsyncMock(return_value=cursor)
    connection.commit = AsyncMock()
    repository = SqliteRepository([connection])

    result = await repository.execute("DELETE FROM users WHERE id = ?", (1,))

    connection.commit.assert_awaited_once()
    assert result == []


@pytest.mark.asyncio
async def test_execute_releases_connection_back_to_pool_after_use(fake_connection):
    repository = SqliteRepository([fake_connection])

    await repository.execute("SELECT * FROM users")

    await asyncio.wait_for(repository.execute("SELECT * FROM users"), timeout=1)


@pytest.mark.asyncio
async def test_concurrent_executes_never_share_the_same_connection_simultaneously():
    connection_a, connection_b = MagicMock(), MagicMock()
    in_use: set[int] = set()

    def make_execute(connection_id: int):
        async def execute(_sql, _params):
            assert connection_id not in in_use
            in_use.add(connection_id)
            await asyncio.sleep(0.01)
            in_use.discard(connection_id)
            cursor = MagicMock()
            cursor.description = None
            return cursor

        return execute

    connection_a.execute = make_execute(1)
    connection_a.commit = AsyncMock()
    connection_b.execute = make_execute(2)
    connection_b.commit = AsyncMock()

    repository = SqliteRepository([connection_a, connection_b])

    await asyncio.gather(*(repository.execute("SELECT 1") for _ in range(4)))
