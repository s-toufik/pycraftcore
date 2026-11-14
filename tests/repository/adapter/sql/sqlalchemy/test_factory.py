import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pycraftcore.repository.adapter.sql.sqlalchemy.adapter import SqlAlchemyRepository
from pycraftcore.repository.adapter.sql.sqlalchemy.factory import SqlAlchemyRepositoryFactory


class CountingBuilder:
    def __init__(self, url: str = "sqlite+aiosqlite://") -> None:
        self._url = url
        self.built: list[AsyncEngine] = []

    def build(self) -> AsyncEngine:
        engine = create_async_engine(self._url)
        self.built.append(engine)
        return engine


@pytest.mark.asyncio
async def test_connection_builds_the_engine_once_and_keeps_it():
    builder = CountingBuilder()
    factory = SqlAlchemyRepositoryFactory(builder)

    first = await factory.connection()
    second = await factory.connection()

    assert first is second
    assert builder.built == [first]
    await factory.disconnect()


@pytest.mark.asyncio
async def test_connect_returns_one_repository_on_the_engine():
    factory = SqlAlchemyRepositoryFactory(CountingBuilder())

    first = await factory.connect()
    second = await factory.connect()

    assert isinstance(first, SqlAlchemyRepository)
    assert first is second
    await factory.disconnect()


@pytest.mark.asyncio
async def test_disconnect_disposes_the_engine_and_a_later_call_builds_a_new_one():
    builder = CountingBuilder()
    factory = SqlAlchemyRepositoryFactory(builder)
    first = await factory.connection()

    await factory.disconnect()
    second = await factory.connection()

    assert second is not first
    assert len(builder.built) == 2
    await factory.disconnect()


@pytest.mark.asyncio
async def test_disconnect_without_an_engine_builds_nothing():
    builder = CountingBuilder()

    await SqlAlchemyRepositoryFactory(builder).disconnect()

    assert builder.built == []


@pytest.mark.asyncio
async def test_ping_succeeds_when_the_database_answers():
    factory = SqlAlchemyRepositoryFactory(CountingBuilder())

    await factory.ping()

    await factory.disconnect()


@pytest.mark.asyncio
async def test_ping_fails_when_the_database_cannot_be_reached(tmp_path):
    missing = tmp_path / "missing" / "main.db"
    factory = SqlAlchemyRepositoryFactory(CountingBuilder(f"sqlite+aiosqlite:///{missing}"))

    with pytest.raises(OperationalError):
        await factory.ping()

    await factory.disconnect()
