import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.node.execution_node import ExecutorNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall
from agentic.adapter.outbound.agent.tool.schema.tool_result import ToolResult
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


def make_state_with_tool_calls(tool_calls):
    return AgentState(
        conversation=Conversation(
            [ConversationMessage(role=Role.ASSISTANT, content="", tool_calls=tool_calls)]
        )
    )


@pytest.mark.asyncio
async def test_no_tool_calls_returns_state_unchanged_except_last_node():
    state = AgentState(conversation=Conversation([ConversationMessage(role=Role.USER, content="hi")]))
    registry = MagicMock()
    node = ExecutorNode(registry)

    result = unpack_state(await node(pack_state(state)))

    assert len(result.conversation.messages) == 1
    assert result.last_node == "executor"


@pytest.mark.asyncio
async def test_unknown_tool_produces_error_result_without_raising():
    state = make_state_with_tool_calls([ToolCall(id="call_1", name="missing_tool", args={})])
    registry = MagicMock()
    registry.get.side_effect = KeyError("missing_tool")
    node = ExecutorNode(registry)

    result = unpack_state(await node(pack_state(state)))

    tool_message = result.conversation.messages[-1]
    assert tool_message.role == Role.TOOL
    assert "Unknown tool" in tool_message.content


@pytest.mark.asyncio
async def test_tool_raising_exception_is_caught_into_tool_result():
    tool = MagicMock()
    tool.args_schema = MagicMock(return_value=MagicMock(call_id=None))
    tool.execute = AsyncMock(side_effect=RuntimeError("boom"))
    registry = MagicMock()
    registry.get.return_value = tool
    state = make_state_with_tool_calls([ToolCall(id="call_1", name="failing_tool", args={})])
    node = ExecutorNode(registry)

    result = unpack_state(await node(pack_state(state)))

    tool_message = result.conversation.messages[-1]
    assert "boom" in tool_message.content


@pytest.mark.asyncio
async def test_successful_tool_results_appended_in_call_order():
    def make_tool(output):
        tool = MagicMock()
        request = MagicMock()
        tool.args_schema = MagicMock(return_value=request)
        tool.execute = AsyncMock(
            return_value=ToolResult(tool_name="t", id="x", output=output, error=None)
        )
        return tool

    tool_a = make_tool("result_a")
    tool_b = make_tool("result_b")
    registry = MagicMock()
    registry.get.side_effect = lambda name: {"tool_a": tool_a, "tool_b": tool_b}[name]
    state = make_state_with_tool_calls(
        [
            ToolCall(id="call_1", name="tool_a", args={}),
            ToolCall(id="call_2", name="tool_b", args={}),
        ]
    )
    node = ExecutorNode(registry)

    result = unpack_state(await node(pack_state(state)))

    tool_messages = [m for m in result.conversation.messages if m.role == Role.TOOL]
    assert [m.content for m in tool_messages] == ["result_a", "result_b"]
