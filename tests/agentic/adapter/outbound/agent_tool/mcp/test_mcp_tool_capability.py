import pytest
from unittest.mock import AsyncMock, MagicMock

from mcp.types import TextContent

from agentic.adapter.outbound.agent_tool.mcp.mcp_tool_capability import McpToolCapability
from agentic.adapter.outbound.agent_tool.mcp.mcp_tool_input_factory import build_tool_input


def make_capability(session):
    args_schema = build_tool_input(
        "search", {"properties": {"query": {"type": "string"}}, "required": ["query"]}
    )
    return McpToolCapability(
        session=session, name="search", description="search the docs", args_schema=args_schema
    )


def make_request(args_schema_capability, query="hello", call_id="call_1"):
    request = args_schema_capability.args_schema(query=query)
    request.call_id = call_id
    return request


def test_schema_reflects_name_description_and_parameters():
    capability = make_capability(MagicMock())

    schema = capability.schema()

    assert schema["name"] == "search"
    assert schema["description"] == "search the docs"
    assert "query" in schema["parameters"]["properties"]


@pytest.mark.asyncio
async def test_execute_returns_the_text_content_on_success():
    session = MagicMock()
    session.call_tool = AsyncMock(
        return_value=MagicMock(
            content=[TextContent(type="text", text="42 results")], is_error=False
        )
    )
    capability = make_capability(session)
    request = make_request(capability)

    result = await capability.execute(request)

    assert result.output == "42 results"
    assert result.error is None
    session.call_tool.assert_awaited_once_with("search", {"query": "hello"})


@pytest.mark.asyncio
async def test_execute_maps_mcp_tool_side_error_to_tool_result_error():
    session = MagicMock()
    session.call_tool = AsyncMock(
        return_value=MagicMock(
            content=[TextContent(type="text", text="invalid query")], is_error=True
        )
    )
    capability = make_capability(session)
    request = make_request(capability)

    result = await capability.execute(request)

    assert result.output == ""
    assert result.error == "invalid query"


@pytest.mark.asyncio
async def test_execute_catches_transport_exceptions():
    session = MagicMock()
    session.call_tool = AsyncMock(side_effect=ConnectionError("mcp server unreachable"))
    capability = make_capability(session)
    request = make_request(capability)

    result = await capability.execute(request)

    assert result.output == ""
    assert "mcp server unreachable" in result.error


@pytest.mark.asyncio
async def test_execute_omits_unset_optional_arguments():
    args_schema = build_tool_input(
        "search",
        {
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    )
    session = MagicMock()
    session.call_tool = AsyncMock(return_value=MagicMock(content=[], is_error=False))
    capability = McpToolCapability(session, "search", "desc", args_schema)
    request = args_schema(query="hi")
    request.call_id = "call_1"

    await capability.execute(request)

    session.call_tool.assert_awaited_once_with("search", {"query": "hi"})
