from pathlib import Path
from sqlite3 import Row
from typing import cast

from aiosqlite import Connection, connect

from agentic_core.infrastructure.repository.sqlite.adapter import SQLiteRepository
from agentic_core.infrastructure.repository.sqlite.schema import SqliteConnector


class SQLiteRepositoryFactory:
    def __init__(self, settings: SqliteConnector):
        self._settings = settings
        self._client: Connection | None = None

    async def connection(self) -> Connection:
        if self._client is None:
            self._create_repository_directory(self._settings.path)
            self._client = await connect(
                self._set_repository_file(self._settings.path, self._settings.default_name)
            )
            self._client.row_factory = Row

        return cast(Connection, self._client)

    async def connect(self) -> SQLiteRepository:
        client = await self.connection()
        return SQLiteRepository(client)

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @staticmethod
    def _create_repository_directory(path: str) -> None:
        path: Path = Path(path)
        if not path.exists():
            path.mkdir(parents=True)

    @staticmethod
    def _set_repository_file(path: str, repository_name: str = "sqlite") -> str:
        return str(Path(path) / f"{repository_name}.db")
