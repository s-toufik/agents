from pathlib import Path
from sqlite3 import Row
from typing import cast

from aiosqlite import Connection, connect

from agentic.infrastructure.repository.sqlite.adapter import SQLiteRepository
from agentic.infrastructure.repository.sqlite.settings import SqliteSettings


class SQLiteRepositoryFactory:
    def __init__(self, settings: SqliteSettings):
        self._settings = settings
        self._client: Connection | None = None

    async def create_client(self) -> Connection:
        if self._client is None:
            self._create_repository_directory(self._settings.database_path)
            self._client = await connect(
                self._set_repository_file(
                    self._settings.database_path, self._settings.database_name
                )
            )
            self._client.row_factory = Row

        return cast(Connection, self._client)

    async def create_repository(self) -> SQLiteRepository:
        client = await self.create_client()
        return SQLiteRepository(client)

    async def close(self) -> None:
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
