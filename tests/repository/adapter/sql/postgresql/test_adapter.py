from unittest.mock import AsyncMock, MagicMock

import pytest

from pycraftcore.repository.adapter.sql.postgresql.adapter import PostgresRepository


def make_column(name: str) -> MagicMock:
    column = MagicMock()
    column.name = name
    return column


@pytest.fixture
def fake_cursor():
    cursor = MagicMock()
    cursor.description = [make_column("id"), make_column("name")]
    cursor.execute = AsyncMock()
    cursor.fetchall = AsyncMock(
        return_value=[
            (1, "John"),
            (2, "Alice"),
        ]
    )
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=False)
    return cursor


@pytest.fixture
def fake_connection(fake_cursor):
    connection = MagicMock()
    connection.cursor.return_value = fake_cursor
    connection.__aenter__ = AsyncMock(return_value=connection)
    connection.__aexit__ = AsyncMock(return_value=False)
    return connection


@pytest.fixture
def fake_pool(fake_connection):
    pool = MagicMock()
    pool.connection.return_value = fake_connection
    return pool


@pytest.fixture
def repository(fake_pool):
    return PostgresRepository(fake_pool)


@pytest.mark.asyncio
async def test_execute_returns_rows_zipped_with_column_names(repository, fake_cursor):
    result = await repository.execute("SELECT * FROM users")

    fake_cursor.execute.assert_awaited_once_with("SELECT * FROM users", ())
    assert result == [
        {"id": 1, "name": "John"},
        {"id": 2, "name": "Alice"},
    ]


@pytest.mark.asyncio
async def test_execute_passes_parameters_through(repository, fake_cursor):
    await repository.execute("SELECT * FROM users WHERE id = %s", (1,))

    fake_cursor.execute.assert_awaited_once_with("SELECT * FROM users WHERE id = %s", (1,))


@pytest.mark.asyncio
async def test_execute_returns_empty_list_when_no_result_set(repository, fake_cursor):
    fake_cursor.description = None

    result = await repository.execute("DELETE FROM users WHERE id = %s", (1,))

    assert result == []


@pytest.mark.asyncio
async def test_execute_acquires_connection_and_cursor_from_pool(
    repository, fake_pool, fake_connection
):
    await repository.execute("SELECT 1")

    fake_pool.connection.assert_called_once()
    fake_connection.cursor.assert_called_once()
