import base64
from contextlib import AsyncExitStack

import httpx2
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from pycraftcore.application_configuration.model.connector import McpConnector
from pycraftcore.authentication import AuthTyping
from pycraftcore.authentication.model.basic_auth import BasicAuth
from pycraftcore.authentication.model.token_auth import TokenAuth


class McpClientFactory:
    def __init__(self, connector: McpConnector) -> None:
        self._connector = connector
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None

    async def start(self) -> None:
        if self._session is not None:
            return

        stack = AsyncExitStack()
        try:
            read, write = await self._connect(stack)
            session = await stack.enter_async_context(ClientSession(read, write))
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
            raise RuntimeError("McpClientFactory session is not started")
        return self._session

    async def _connect(self, stack: AsyncExitStack):
        headers = self._headers()

        if self._connector.transport == "sse":
            return await stack.enter_async_context(
                sse_client(
                    self._connector.base_url, headers=headers, timeout=self._connector.timeout
                )
            )

        http_client = create_mcp_http_client(
            headers=headers, timeout=httpx2.Timeout(self._connector.timeout)
        )
        await stack.enter_async_context(http_client)
        return await stack.enter_async_context(
            streamable_http_client(self._connector.base_url, http_client=http_client)
        )

    def _headers(self) -> dict[str, str]:
        auth: AuthTyping = self._connector.auth
        if isinstance(auth, TokenAuth):
            return {auth.key_name: auth.key_value}
        if isinstance(auth, BasicAuth):
            token = base64.b64encode(f"{auth.username}:{auth.password}".encode()).decode()
            return {"Authorization": f"Basic {token}"}
        return {}
