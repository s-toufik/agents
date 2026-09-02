import pytest
from unittest.mock import AsyncMock

from mcp.server.mcpserver import MCPServer

from agentic.adapter.outbound.agent_tool.mcp.mcp_in_process_client_factory import (
    McpInProcessClientFactory,
)


def make_server() -> MCPServer:
    server = MCPServer(name="test")

    @server.tool(name="echo", description="echoes input")
    async def echo(value: str) -> str:
        return f"echo: {value}"

    return server


@pytest.mark.asyncio
async def test_start_connects_and_lists_the_real_registered_tools():
    factory = McpInProcessClientFactory(make_server())

    await factory.start()
    session = factory.create_client()
    tools = await session.list_tools()

    assert [tool.name for tool in tools.tools] == ["echo"]

    await factory.close()


@pytest.mark.asyncio
async def test_calling_a_tool_through_the_in_process_session_returns_the_real_result():
    factory = McpInProcessClientFactory(make_server())
    await factory.start()
    session = factory.create_client()

    result = await session.call_tool("echo", {"value": "hello"})

    assert result.is_error is False
    assert result.content[0].text == "echo: hello"

    await factory.close()


@pytest.mark.asyncio
async def test_start_is_idempotent():
    factory = McpInProcessClientFactory(make_server())

    await factory.start()
    first_session = factory.create_client()
    await factory.start()
    second_session = factory.create_client()

    assert first_session is second_session

    await factory.close()


def test_create_client_raises_before_start():
    factory = McpInProcessClientFactory(make_server())

    with pytest.raises(RuntimeError):
        factory.create_client()


@pytest.mark.asyncio
async def test_close_tears_down_and_allows_a_fresh_start():
    factory = McpInProcessClientFactory(make_server())
    await factory.start()
    first_session = factory.create_client()

    await factory.close()
    with pytest.raises(RuntimeError):
        factory.create_client()

    await factory.start()
    second_session = factory.create_client()
    assert second_session is not first_session
    tools = await second_session.list_tools()
    assert [tool.name for tool in tools.tools] == ["echo"]

    await factory.close()


@pytest.mark.asyncio
async def test_close_before_start_is_a_no_op():
    factory = McpInProcessClientFactory(make_server())

    await factory.close()  # must not raise


@pytest.mark.asyncio
async def test_start_failure_cleans_up_without_leaking_the_background_task(monkeypatch):
    factory = McpInProcessClientFactory(make_server())
    # Simulate the handshake itself failing after the transport/task are already up.
    monkeypatch.setattr(
        "agentic.adapter.outbound.agent_tool.mcp.mcp_in_process_client_factory.ClientSession.initialize",
        AsyncMock(side_effect=ConnectionError("handshake failed")),
    )

    with pytest.raises(ConnectionError):
        await factory.start()

    with pytest.raises(RuntimeError):
        factory.create_client()
