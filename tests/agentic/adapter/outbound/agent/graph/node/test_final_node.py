import pytest

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.node.final_node import FinalNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


@pytest.mark.asyncio
async def test_final_answer_set_from_last_assistant_message():
    state = AgentState(
        conversation=Conversation(
            [ConversationMessage(role=Role.ASSISTANT, content="the answer")]
        )
    )

    result = unpack_state(await FinalNode()(pack_state(state)))

    assert result.final_answer == "the answer"
    assert result.last_node == "final"


@pytest.mark.asyncio
async def test_final_answer_fallback_when_no_assistant_message():
    state = AgentState(conversation=Conversation())

    result = unpack_state(await FinalNode()(pack_state(state)))

    assert result.final_answer == "No answer was produced."
