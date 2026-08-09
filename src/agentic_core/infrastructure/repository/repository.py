from __future__ import annotations

from typing import Any, Protocol


class AsyncSQLRepository(Protocol):
    async def execute(
        self,
        sql: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]: ...


class RepositoryFactory(Protocol):
    async def connection(self) -> Any: ...
    async def disconnect(self) -> None: ...
    async def connect(self) -> AsyncSQLRepository: ...
