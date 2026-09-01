import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Iterable

from aiosqlite import Row, Connection


class SqliteRepository:
    def __init__(self, connections: list[Connection]):
        self._pool: asyncio.Queue[Connection] = asyncio.Queue()
        for connection in connections:
            self._pool.put_nowait(connection)

    @asynccontextmanager
    async def _acquire(self) -> AsyncIterator[Connection]:
        connection = await self._pool.get()
        try:
            yield connection
        finally:
            self._pool.put_nowait(connection)

    async def execute(
        self,
        sql: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        async with self._acquire() as connection:
            cursor = await connection.execute(sql, parameters)
            try:
                if cursor.description is None:
                    await connection.commit()
                    return []

                rows: Iterable[Row] = await cursor.fetchall()

                return [dict(row) for row in rows]
            finally:
                await cursor.close()