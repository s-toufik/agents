import pytest
from unittest.mock import MagicMock

from langchain_core.messages import AIMessageChunk

from agentic.adapter.outbound.agent.graph.node.streaming_planner_node import StreamingPlannerNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


def make_llm(chunks):
    async def chunk_generator(*_args, **_kwargs):
        for chunk in chunks:
            yield chunk

    llm = MagicMock()
    bound = MagicMock()
    bound.astream = chunk_generator
    llm.bind_tools.return_value = bound
    return llm


def make_prompt_service():
    prompt_service = MagicMock()
    prompt_service.planner_system_prompt.return_value = "system"
    return prompt_service


def make_registry():
    registry = MagicMock()
    registry.descriptions.return_value = []
    return registry


@pytest.mark.asyncio
async def test_accumulates_chunks_and_calls_on_token_for_each_nonempty_chunk():
    chunks = [
        AIMessageChunk(content="Hello"),
        AIMessageChunk(content=" world"),
        AIMessageChunk(content=""),
    ]
    llm = make_llm(chunks)
    received_tokens = []

    async def on_token(value):
        received_tokens.append(value)

    node = StreamingPlannerNode(llm, make_registry(), make_prompt_service(), on_token=on_token)
    state = AgentState()

    result = unpack_state(await node(pack_state(state)))

    assert received_tokens == ["Hello", " world"]
    assert result.planner.answer == "Hello world"


@pytest.mark.asyncio
async def test_no_on_token_callback_does_not_raise():
    chunks = [AIMessageChunk(content="Hi")]
    llm = make_llm(chunks)
    node = StreamingPlannerNode(llm, make_registry(), make_prompt_service(), on_token=None)
    state = AgentState()

    result = unpack_state(await node(pack_state(state)))

    assert result.planner.answer == "Hi"


@pytest.mark.asyncio
async def test_tool_calls_in_final_chunk_set_answer_to_none():
    chunks = [
        AIMessageChunk(
            content="",
            tool_call_chunks=[
                {"id": "ignored", "name": "tool_a", "args": "{}", "index": 0}
            ],
        )
    ]
    llm = make_llm(chunks)
    node = StreamingPlannerNode(llm, make_registry(), make_prompt_service(), on_token=None)
    state = AgentState()

    result = unpack_state(await node(pack_state(state)))

    assert result.planner.answer is None
    assert len(result.planner.tool_calls) == 1
    assert result.planner.tool_calls[0].name == "tool_a"
