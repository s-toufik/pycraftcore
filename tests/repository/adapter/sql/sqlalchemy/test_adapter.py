import pytest
from sqlalchemy.exc import IntegrityError

from pycraftcore.repository.adapter.sql.sqlalchemy.factory import SqlAlchemyRepositoryFactory
from pycraftcore.repository.adapter.sql.sqlalchemy.sqlite_engine_builder import (
    SqliteEngineBuilder,
)
from pycraftcore.repository.adapter.sql.sqlite.schema import SqliteConnector
from pycraftcore.repository.port.repository import AsyncRepository


@pytest.fixture
def factory(tmp_path) -> SqlAlchemyRepositoryFactory:
    settings = SqliteConnector(path=str(tmp_path), default_name="main", max_pool_size=1)
    return SqlAlchemyRepositoryFactory(SqliteEngineBuilder(settings))


async def users(factory: SqlAlchemyRepositoryFactory) -> AsyncRepository:
    repository = await factory.connect()
    await repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
    return repository


@pytest.mark.asyncio
async def test_rows_come_back_as_dicts_keyed_by_column(factory):
    repository = await users(factory)
    await repository.execute("INSERT INTO users VALUES (?, ?)", (1, "a@example.com"))

    rows = await repository.execute("SELECT id, email FROM users WHERE id = ?", (1,))

    assert rows == [{"id": 1, "email": "a@example.com"}]
    await factory.disconnect()


@pytest.mark.asyncio
async def test_a_statement_without_rows_returns_nothing_and_is_committed(factory):
    repository = await users(factory)

    written = await repository.execute("INSERT INTO users VALUES (?, ?)", (1, "a@example.com"))
    await factory.disconnect()
    reopened = await factory.connect()

    assert written == []
    assert await reopened.execute("SELECT COUNT(*) AS n FROM users") == [{"n": 1}]
    await factory.disconnect()


@pytest.mark.asyncio
async def test_a_failing_statement_raises_and_writes_nothing(factory):
    repository = await users(factory)
    await repository.execute("INSERT INTO users VALUES (?, ?)", (1, "a@example.com"))

    with pytest.raises(IntegrityError):
        await repository.execute("INSERT INTO users VALUES (?, ?)", (1, "b@example.com"))

    assert await repository.execute("SELECT email FROM users") == [{"email": "a@example.com"}]
    await factory.disconnect()
