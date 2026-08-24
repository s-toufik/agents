import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic.adapter.outbound.agent.enum.reflection_action import ReflectionAction
from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.node.reflection_node import ReflectionNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.reflection_decision import ReflectionDecision
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


def make_llm(decision):
    llm = MagicMock()
    structured = MagicMock()
    structured.ainvoke = AsyncMock(
        return_value={"raw": MagicMock(), "parsed": decision, "parsing_error": None}
    )
    llm.with_structured_output.return_value = structured
    return llm


@pytest.mark.asyncio
async def test_reflection_decision_is_stored_on_state():
    decision = ReflectionDecision(action=ReflectionAction.RETRY, critique="needs work")
    llm = make_llm(decision)
    prompt_service = MagicMock()
    prompt_service.reflection_system_prompt.return_value = "system"
    node = ReflectionNode(llm, prompt_service)
    state = AgentState(
        conversation=Conversation([ConversationMessage(role=Role.ASSISTANT, content="answer")])
    )

    result = unpack_state(await node(pack_state(state)))

    assert result.reflection.action == ReflectionAction.RETRY
    assert result.reflection.critique == "needs work"
    assert result.last_node == "reflection"


@pytest.mark.asyncio
async def test_uses_fallback_text_when_no_assistant_answer():
    decision = ReflectionDecision(action=ReflectionAction.ACCEPT, critique="ok")
    llm = make_llm(decision)
    prompt_service = MagicMock()
    prompt_service.reflection_system_prompt.return_value = "system"
    node = ReflectionNode(llm, prompt_service)
    state = AgentState(conversation=Conversation())

    await node(pack_state(state))

    structured = llm.with_structured_output.return_value
    human_message = structured.ainvoke.call_args[0][0][1]
    assert "(no assistant answer found)" in human_message.content
