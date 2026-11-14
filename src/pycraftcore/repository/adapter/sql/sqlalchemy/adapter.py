from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine


class SqlAlchemyRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def execute(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        async with self._engine.begin() as connection:
            result = await connection.exec_driver_sql(query, parameters)

            if not result.returns_rows:
                return []

            return [dict(row) for row in result.mappings().all()]
