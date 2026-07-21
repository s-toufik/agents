from __future__ import annotations

from typing import Any, Protocol


class AsyncSQLRepository(Protocol):
    async def execute(
        self,
        sql: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]: ...


class RepositoryFactory(Protocol):
    async def create_client(self) -> Any: ...

    async def create_repository(self) -> AsyncSQLRepository: ...
