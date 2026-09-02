import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic.adapter.outbound.agent_tool.mcp.mcp_tool_capability import McpToolCapability
from agentic.adapter.outbound.agent_tool.mcp.mcp_tool_provider import McpToolProvider


def make_mcp_tool(name, description="", input_schema=None):
    # MagicMock's own `name=` kwarg sets its repr, not a `.name` attribute --
    # it has to be assigned separately afterward.
    tool = MagicMock()
    tool.name = name
    tool.description = description
    tool.input_schema = input_schema or {}
    return tool


@pytest.mark.asyncio
async def test_tools_wraps_every_discovered_mcp_tool():
    session = MagicMock()
    tool_a = make_mcp_tool("search")
    tool_b = make_mcp_tool("fetch")
    session.list_tools = AsyncMock(return_value=MagicMock(tools=[tool_a, tool_b]))

    client_factory = MagicMock()
    client_factory.create_client.return_value = session

    tools = await McpToolProvider(client_factory).tools()

    assert len(tools) == 2
    assert all(isinstance(tool, McpToolCapability) for tool in tools)
    assert {tool.name for tool in tools} == {"search", "fetch"}


@pytest.mark.asyncio
async def test_tools_returns_empty_list_when_server_has_no_tools():
    session = MagicMock()
    session.list_tools = AsyncMock(return_value=MagicMock(tools=[]))
    client_factory = MagicMock()
    client_factory.create_client.return_value = session

    tools = await McpToolProvider(client_factory).tools()

    assert tools == []


@pytest.mark.asyncio
async def test_tool_description_defaults_to_empty_string_when_none():
    session = MagicMock()
    tool = MagicMock()
    tool.name = "search"
    tool.description = None
    tool.input_schema = {}
    session.list_tools = AsyncMock(return_value=MagicMock(tools=[tool]))
    client_factory = MagicMock()
    client_factory.create_client.return_value = session

    tools = await McpToolProvider(client_factory).tools()

    assert tools[0].schema()["description"] == ""
