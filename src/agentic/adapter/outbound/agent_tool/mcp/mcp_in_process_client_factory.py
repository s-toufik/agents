import asyncio
import contextlib
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.server.mcpserver import MCPServer
from mcp.shared.memory import create_client_server_memory_streams


class McpInProcessClientFactory:

    def __init__(self, server: MCPServer) -> None:
        self._server = server
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None

    async def start(self) -> None:
        if self._session is not None:
            return

        stack = AsyncExitStack()
        try:
            client_streams, server_streams = await stack.enter_async_context(
                create_client_server_memory_streams()
            )
            client_read, client_write = client_streams
            server_read, server_write = server_streams

            lowlevel = self._server._lowlevel_server
            server_task = asyncio.create_task(
                lowlevel.run(server_read, server_write, lowlevel.create_initialization_options())
            )
            stack.push_async_callback(self._cancel, server_task)

            session = await stack.enter_async_context(ClientSession(client_read, client_write))
            await session.initialize()
        except BaseException:
            await stack.aclose()
            raise

        self._stack = stack
        self._session = session

    async def close(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
        self._stack = None
        self._session = None

    def create_client(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("McpInProcessClientFactory session is not started")
        return self._session

    @staticmethod
    async def _cancel(task: asyncio.Task) -> None:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
