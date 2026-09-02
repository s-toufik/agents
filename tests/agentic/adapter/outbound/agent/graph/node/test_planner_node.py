import pytest
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import AIMessage, AIMessageChunk

from agentic.adapter.outbound.agent.graph.node.planner_node import PlannerNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


def make_prompt_service():
    prompt_service = MagicMock()
    prompt_service.planner_system_prompt.return_value = "system"
    return prompt_service


def make_registry():
    registry = MagicMock()
    registry.descriptions.return_value = []
    return registry


def make_llm(ai_message):
    llm = MagicMock()
    bound = MagicMock()
    bound.ainvoke = AsyncMock(return_value=ai_message)
    llm.bind_tools.return_value = bound
    return llm


def make_streaming_llm(chunks):
    async def chunk_generator(*_args, **_kwargs):
        for chunk in chunks:
            yield chunk

    llm = MagicMock()
    bound = MagicMock()
    bound.astream = chunk_generator
    llm.bind_tools.return_value = bound
    return llm


@pytest.mark.asyncio
async def test_tool_calls_present_sets_answer_none_and_tracks_iteration():
    ai_message = AIMessage(
        content="",
        tool_calls=[{"id": "ignored", "name": "tool_a", "args": {"x": 1}}],
    )
    node = PlannerNode(make_llm(ai_message), make_registry(), make_prompt_service())
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
    node = PlannerNode(make_llm(ai_message), make_registry(), make_prompt_service())
    state = AgentState()

    result = unpack_state(await node(pack_state(state)))

    assert result.planner.answer == "final answer"
    assert result.planner.tool_calls == []


@pytest.mark.asyncio
async def test_streaming_accumulates_chunks_and_calls_on_token_for_each_nonempty_chunk():
    chunks = [
        AIMessageChunk(content="Hello"),
        AIMessageChunk(content=" world"),
        AIMessageChunk(content=""),
    ]
    llm = make_streaming_llm(chunks)
    received_tokens = []

    async def on_token(value):
        received_tokens.append(value)

    node = PlannerNode(llm, make_registry(), make_prompt_service(), on_token=on_token)
    state = AgentState()

    result = unpack_state(await node(pack_state(state)))

    assert received_tokens == ["Hello", " world"]
    assert result.planner.answer == "Hello world"


@pytest.mark.asyncio
async def test_no_on_token_uses_the_non_streaming_path():
    # on_token=None (the default) must not call .astream() at all -- it's
    # what selects the plain .ainvoke() path.
    ai_message = AIMessage(content="Hi", tool_calls=[])
    llm = make_llm(ai_message)
    node = PlannerNode(llm, make_registry(), make_prompt_service(), on_token=None)
    state = AgentState()

    result = unpack_state(await node(pack_state(state)))

    assert result.planner.answer == "Hi"
    llm.bind_tools.return_value.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_streaming_tool_calls_in_final_chunk_set_answer_to_none():
    chunks = [
        AIMessageChunk(
            content="",
            tool_call_chunks=[{"id": "ignored", "name": "tool_a", "args": "{}", "index": 0}],
        )
    ]

    async def on_token(_value):
        pass

    node = PlannerNode(
        make_streaming_llm(chunks), make_registry(), make_prompt_service(), on_token=on_token
    )
    state = AgentState()

    result = unpack_state(await node(pack_state(state)))

    assert result.planner.answer is None
    assert len(result.planner.tool_calls) == 1
    assert result.planner.tool_calls[0].name == "tool_a"
