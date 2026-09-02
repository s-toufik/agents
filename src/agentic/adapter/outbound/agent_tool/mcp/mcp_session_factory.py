from typing import Protocol

from mcp import ClientSession


class McpSessionFactory(Protocol):

    async def start(self) -> None: ...
    async def close(self) -> None: ...
    def create_client(self) -> ClientSession: ...
