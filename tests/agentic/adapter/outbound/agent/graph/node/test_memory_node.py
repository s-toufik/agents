import pytest

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.node.memory_node import MemoryNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


def make_conversation(n):
    messages = [
        ConversationMessage(role=Role.USER if i % 2 == 0 else Role.ASSISTANT, content=f"msg{i}")
        for i in range(n)
    ]
    return Conversation(messages)


@pytest.mark.asyncio
async def test_trims_conversation_to_fit_under_max_tokens():
    state = AgentState(conversation=make_conversation(10))
    node = MemoryNode(max_context_tokens=15)

    result = unpack_state(await node(pack_state(state)))

    assert len(result.conversation.messages) < 10
    assert result.conversation.messages[-1].content == "msg9"
    assert result.last_node == "memory"


@pytest.mark.asyncio
async def test_keeps_all_messages_when_well_under_max_tokens():
    state = AgentState(conversation=make_conversation(2))
    node = MemoryNode(max_context_tokens=8_000)

    result = unpack_state(await node(pack_state(state)))

    assert len(result.conversation.messages) == 2
