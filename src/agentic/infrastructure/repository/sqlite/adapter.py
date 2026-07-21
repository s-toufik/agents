from typing import Iterable

from aiosqlite import Row, Connection
from typing import Any


class SQLiteRepository:
    def __init__(self, client: Connection):
        self._client = client

    async def execute(
        self,
        sql: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        cursor = await self._client.execute(sql, parameters)

        if cursor.description is None:
            await self._client.commit()
            return []

        rows: Iterable[Row] = await cursor.fetchall()

        return [dict(row) for row in rows]
