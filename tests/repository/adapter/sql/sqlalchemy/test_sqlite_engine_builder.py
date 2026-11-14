import pytest

from pycraftcore.repository.adapter.sql.sqlalchemy.sqlite_engine_builder import (
    SqliteEngineBuilder,
)
from pycraftcore.repository.adapter.sql.sqlite.schema import SqliteConnector


def make_builder(directory, max_pool_size: int = 2) -> SqliteEngineBuilder:
    return SqliteEngineBuilder(
        SqliteConnector(path=str(directory), default_name="main", max_pool_size=max_pool_size)
    )


def test_the_engine_points_at_the_prepared_database_file_through_aiosqlite(tmp_path):
    directory = tmp_path / "data"

    url = make_builder(directory).build().url

    assert url.drivername == "sqlite+aiosqlite"
    assert url.database == str(directory / "main.db")
    assert directory.is_dir()


def test_the_pool_holds_at_most_max_pool_size_connections(tmp_path):
    pool = make_builder(tmp_path, max_pool_size=4).build().pool

    assert pool.size() == 4
    assert pool._max_overflow == 0


@pytest.mark.asyncio
async def test_every_connection_gets_the_shared_pragmas(tmp_path):
    engine = make_builder(tmp_path).build()

    async with engine.connect() as connection:
        journal = (await connection.exec_driver_sql("PRAGMA journal_mode")).scalar()
        timeout = (await connection.exec_driver_sql("PRAGMA busy_timeout")).scalar()
        synchronous = (await connection.exec_driver_sql("PRAGMA synchronous")).scalar()

    assert (journal, timeout, synchronous) == ("wal", 5000, 1)
    await engine.dispose()
