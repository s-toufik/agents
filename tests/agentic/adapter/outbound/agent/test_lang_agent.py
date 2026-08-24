import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.lang_agent import LangAgent
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.service.state_serialization import pack_state
from agentic.domain.model.agent_request import AgentRequest


def make_graph(snapshot_values, invoke_result_state):
    graph = MagicMock()
    snapshot = MagicMock()
    snapshot.values = snapshot_values
    graph.aget_state = AsyncMock(return_value=snapshot)
    graph.ainvoke = AsyncMock(return_value=pack_state(invoke_result_state))
    return graph


@pytest.mark.asyncio
async def test_starts_fresh_state_when_no_prior_snapshot():
    result_state = AgentState(session_id="s1", final_answer="hi there", iteration=1)
    graph = make_graph(snapshot_values=None, invoke_result_state=result_state)
    agent = LangAgent({"gpt": graph})
    request = AgentRequest(message="hello", model_name="gpt", request_id="s1")

    message = await agent.run(request)

    assert message.content == "hi there"
    assert message.session_id == "s1"
    assert message.metadata == {"iteration": "1", "max_iteration": "20"}

    invoked_state = graph.ainvoke.call_args[0][0]["state"]
    assert invoked_state["conversation"][-1]["role"] == "user"
    assert invoked_state["conversation"][-1]["content"] == "hello"


@pytest.mark.asyncio
async def test_resumes_from_existing_snapshot_and_resets_iteration():
    prior_state = AgentState(
        session_id="s1",
        iteration=7,
        conversation=Conversation([ConversationMessage(role=Role.USER, content="earlier")]),
    )
    result_state = AgentState(session_id="s1", final_answer="resumed answer")
    graph = make_graph(snapshot_values=pack_state(prior_state), invoke_result_state=result_state)
    agent = LangAgent({"gpt": graph})
    request = AgentRequest(message="new message", model_name="gpt", request_id="s1")

    await agent.run(request)

    invoked_state = graph.ainvoke.call_args[0][0]["state"]
    assert invoked_state["iteration"] == 0
    assert invoked_state["conversation"][-1]["content"] == "new message"
    assert invoked_state["conversation"][0]["content"] == "earlier"


@pytest.mark.asyncio
async def test_unknown_model_name_raises_key_error():
    agent = LangAgent({})
    request = AgentRequest(message="hi", model_name="unknown", request_id="s1")

    with pytest.raises(KeyError):
        await agent.run(request)
