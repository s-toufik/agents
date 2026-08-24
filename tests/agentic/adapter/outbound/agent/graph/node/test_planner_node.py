import pytest
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import AIMessage

from agentic.adapter.outbound.agent.graph.node.planner_node import PlannerNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


def make_llm(ai_message):
    llm = MagicMock()
    bound = MagicMock()
    bound.ainvoke = AsyncMock(return_value=ai_message)
    llm.bind_tools.return_value = bound
    return llm


@pytest.mark.asyncio
async def test_tool_calls_present_sets_answer_none_and_tracks_iteration():
    ai_message = AIMessage(
        content="",
        tool_calls=[{"id": "ignored", "name": "tool_a", "args": {"x": 1}}],
    )
    llm = make_llm(ai_message)
    registry = MagicMock()
    registry.descriptions.return_value = []
    prompt_service = MagicMock()
    prompt_service.planner_system_prompt.return_value = "system"
    node = PlannerNode(llm, registry, prompt_service)
    state = AgentState(iteration=0)

    result = unpack_state(await node(pack_state(state)))

    assert result.planner.answer is None
    assert len(result.planner.tool_calls) == 1
    assert result.planner.tool_calls[0].name == "tool_a"
    assert result.planner.tool_calls[0].id.startswith("call_")
    assert result.iteration == 1
    assert result.last_node == "planner"


@pytest.mark.asyncio
async def test_no_tool_calls_sets_answer_from_content():
    ai_message = AIMessage(content="final answer", tool_calls=[])
    llm = make_llm(ai_message)
    registry = MagicMock()
    registry.descriptions.return_value = []
    prompt_service = MagicMock()
    prompt_service.planner_system_prompt.return_value = "system"
    node = PlannerNode(llm, registry, prompt_service)
    state = AgentState()

    result = unpack_state(await node(pack_state(state)))

    assert result.planner.answer == "final answer"
    assert result.planner.tool_calls == []
