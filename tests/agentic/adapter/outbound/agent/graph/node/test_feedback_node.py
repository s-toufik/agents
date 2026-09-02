import pytest
from unittest.mock import MagicMock

from agentic.adapter.outbound.agent.enum.reflection_action import ReflectionAction
from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.node.feedback_node import FeedbackNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.reflection_decision import ReflectionDecision
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


@pytest.mark.asyncio
async def test_appends_critique_from_reflection_when_present():
    prompt_service = MagicMock()
    prompt_service.feedback_system_prompt.return_value = "please fix: too vague"
    node = FeedbackNode(prompt_service)
    state = AgentState(
        reflection=ReflectionDecision(action=ReflectionAction.RETRY, critique="too vague")
    )

    result = unpack_state(await node(pack_state(state)))

    prompt_service.feedback_system_prompt.assert_called_once_with("too vague")
    assert result.conversation.messages[-1].role == Role.USER
    assert result.conversation.messages[-1].content == "please fix: too vague"
    assert result.last_node == "feedback"


@pytest.mark.asyncio
async def test_uses_fallback_critique_when_reflection_is_none():
    prompt_service = MagicMock()
    prompt_service.feedback_system_prompt.return_value = "generic feedback"
    node = FeedbackNode(prompt_service)
    state = AgentState(reflection=None)

    await node(pack_state(state))

    prompt_service.feedback_system_prompt.assert_called_once_with("No specific critique provided.")
