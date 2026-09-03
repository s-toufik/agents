from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse


def build_mcp_server(
    name: str,
    version: str,
    instructions: str | None = None,
    lifespan: Callable[[MCPServer], AbstractAsyncContextManager[Any]] | None = None,
) -> MCPServer:

    server = MCPServer(
        name=name,
        version=version,
        instructions=instructions,
        lifespan=lifespan,
    )

    @server.custom_route("/health", methods=["GET"])
    async def health(_: Request) -> JSONResponse:
        tools = await server.list_tools()
        if not tools:
            return JSONResponse({"status": "starting", "tools": 0}, status_code=503)
        return JSONResponse({"status": "ok", "tools": [tool.name for tool in tools]})

    return server
