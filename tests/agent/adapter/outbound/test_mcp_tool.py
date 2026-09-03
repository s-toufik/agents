from typing import cast

import pytest
from mcp import ClientSession
from mcp.types import CallToolResult, TextContent

from agent.adapter.outbound.tool.mcp.mcp_tool import McpTool
from agent.adapter.outbound.tool.mcp.mcp_tool_provider import McpToolProvider
from agent.domain.exception.tool_unavailable_exception import ToolUnavailableException
from agent.domain.model.tool_invocation import ToolInvocation
from agent.domain.model.tool_specification import ToolSpecification

SPEC = ToolSpecification(name="run_sql", description="SQL.", parameters={"type": "object"})


class StubSession:
    def __init__(self, result=None, error: Exception | None = None, tools=None) -> None:
        self._result = result
        self._error = error
        self._tools = tools or []
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, arguments: dict | None = None):
        self.calls.append((name, arguments or {}))
        if self._error:
            raise self._error
        return self._result

    async def list_tools(self):
        class Response:
            tools = self._tools

        return Response()


class StubFactory:
    def __init__(self, session: StubSession) -> None:
        self._session = session
        self.invalidated = False

    async def start(self) -> None: ...

    async def close(self) -> None: ...

    async def session(self) -> ClientSession:
        # StubSession duck-types the two ClientSession methods McpTool/McpToolProvider
        # actually call (call_tool, list_tools); this cast keeps the real return type
        # in the signature for McpSessionFactory's Protocol check without pulling in
        # a full ClientSession here.
        return cast(ClientSession, self._session)

    async def invalidate(self) -> None:
        self.invalidated = True


def text_result(text: str, is_error: bool = False) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=text)], is_error=is_error)


async def test_forwards_arguments_untouched() -> None:
    session = StubSession(result=text_result("ok"))
    tool = McpTool(StubFactory(session), SPEC)

    await tool.invoke(ToolInvocation(id="1", name="run_sql", arguments={"query": "select 1"}))

    assert session.calls == [("run_sql", {"query": "select 1"})]


async def test_error_result_becomes_a_failed_outcome() -> None:
    tool = McpTool(StubFactory(StubSession(result=text_result("nope", is_error=True))), SPEC)

    outcome = await tool.invoke(ToolInvocation(id="1", name="run_sql"))

    assert outcome.error == "nope"


async def test_transport_failure_invalidates_the_session() -> None:
    factory = StubFactory(StubSession(error=ConnectionError("gone")))
    tool = McpTool(factory, SPEC)

    outcome = await tool.invoke(ToolInvocation(id="1", name="run_sql"))

    assert factory.invalidated
    assert outcome.error is not None
    assert "gone" in outcome.error


async def test_provider_rejects_an_empty_catalogue() -> None:
    provider = McpToolProvider(StubFactory(StubSession(tools=[])))

    with pytest.raises(ToolUnavailableException):
        await provider.tools()
