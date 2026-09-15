from typing import Any, LiteralString, cast

from psycopg_pool import AsyncConnectionPool


class PostgresRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def execute(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        async with self._pool.connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(cast(LiteralString, query), parameters)

                if cursor.description is None:
                    return []

                rows: list[Any] = await cursor.fetchall()

                column_names: list[str] = [column.name for column in cursor.description]  # type: ignore

                return [dict(zip(column_names, row)) for row in rows]
