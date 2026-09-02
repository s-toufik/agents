import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic.adapter.outbound.agent_tool.mcp.server.mcp_tool_server_factory import (
    build_mcp_server,
    register_tools,
)
from agentic.adapter.outbound.agent_tool.schema.tool_result import ToolResult


def make_capability(name: str, description: str, output: str = "", error: str | None = None):
    capability = MagicMock()
    capability.name = name
    capability.schema.return_value = {
        "name": name,
        "description": description,
        "parameters": {},
    }
    capability.execute = AsyncMock(
        return_value=ToolResult(tool_name=name, id="mcp", output=output, error=error)
    )
    return capability


@pytest.mark.asyncio
async def test_registers_exactly_the_two_tools_with_their_own_names_and_descriptions():
    sql_tool = make_capability("users_tables", "query the users db")
    python_tool = make_capability("python_executor", "run python")
    server = build_mcp_server("agentic")

    register_tools(server, sql_tool, python_tool)
    tools = await server.list_tools()

    assert {tool.name: tool.description for tool in tools} == {
        "users_tables": "query the users db",
        "python_executor": "run python",
    }


@pytest.mark.asyncio
async def test_calling_the_sql_tool_through_the_server_delegates_to_the_capability():
    sql_tool = make_capability("users_tables", "query the users db", output="[{'id': 1}]")
    python_tool = make_capability("python_executor", "run python")
    server = build_mcp_server("agentic")
    register_tools(server, sql_tool, python_tool)

    result = await server.call_tool("users_tables", {"query": "SELECT 1", "dialect": "sqlite"})

    assert result.content[0].text == "[{'id': 1}]"
    sql_tool.execute.assert_awaited_once()
    request = sql_tool.execute.await_args.args[0]
    assert request.query == "SELECT 1"
    assert request.dialect == "sqlite"


@pytest.mark.asyncio
async def test_calling_the_python_tool_through_the_server_delegates_to_the_capability():
    sql_tool = make_capability("users_tables", "query the users db")
    python_tool = make_capability("python_executor", "run python", output='{"result": 4}')
    server = build_mcp_server("agentic")
    register_tools(server, sql_tool, python_tool)

    result = await server.call_tool("python_executor", {"code": "result = 2 + 2"})

    assert result.content[0].text == '{"result": 4}'
    request = python_tool.execute.await_args.args[0]
    assert request.code == "result = 2 + 2"


@pytest.mark.asyncio
async def test_capability_error_is_surfaced_as_the_tool_result_content():
    # ToolResult.content already formats "Error: ..." the same way the native
    # ReAct path sees it -- the MCP wrapper doesn't introduce a second convention.
    sql_tool = make_capability("users_tables", "query the users db", error="bad query")
    python_tool = make_capability("python_executor", "run python")
    server = build_mcp_server("agentic")
    register_tools(server, sql_tool, python_tool)

    result = await server.call_tool("users_tables", {"query": "bad", "dialect": "sqlite"})

    assert result.content[0].text == "Error: bad query"
