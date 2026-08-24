from agentic.adapter.outbound.agent.enum.reflection_action import ReflectionAction
from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.planner_decision import PlannerDecision
from agentic.adapter.outbound.agent.graph.schema.reflection_decision import ReflectionDecision
from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state


def test_pack_state_serializes_conversation_planner_and_reflection():
    state = AgentState(
        conversation=Conversation(
            [
                ConversationMessage(
                    role=Role.ASSISTANT,
                    content="hi",
                    tool_calls=[ToolCall(id="1", name="tool", args={"a": 1})],
                )
            ]
        ),
        planner=PlannerDecision(answer="ok"),
        reflection=ReflectionDecision(action=ReflectionAction.ACCEPT, critique="fine"),
        last_node="reflection",
        session_id="s1",
        iteration=2,
        max_iterations=10,
        final_answer="final",
    )

    graph_state = pack_state(state)

    inner = graph_state["state"]
    assert inner["conversation"][0]["role"] == "assistant"
    assert inner["conversation"][0]["tool_calls"][0]["id"] == "1"
    assert inner["planner"]["answer"] == "ok"
    assert inner["reflection"]["action"] == "accept"
    assert inner["last_node"] == "reflection"
    assert inner["session_id"] == "s1"
    assert inner["iteration"] == 2
    assert inner["max_iterations"] == 10
    assert inner["final_answer"] == "final"


def test_pack_state_planner_and_reflection_none_when_absent():
    state = AgentState()

    graph_state = pack_state(state)

    assert graph_state["state"]["planner"] is None
    assert graph_state["state"]["reflection"] is None


def test_unpack_state_round_trips_pack_state_output():
    original = AgentState(
        conversation=Conversation([ConversationMessage(role=Role.USER, content="hi")]),
        planner=PlannerDecision(answer="ok"),
        reflection=ReflectionDecision(action=ReflectionAction.RETRY, critique="try again"),
        last_node="planner",
        session_id="s1",
        iteration=3,
        max_iterations=8,
        final_answer=None,
    )

    restored = unpack_state(pack_state(original))

    assert restored.conversation.messages[0].content == "hi"
    assert restored.planner.answer == "ok"
    assert restored.reflection.critique == "try again"
    assert restored.last_node == "planner"
    assert restored.session_id == "s1"
    assert restored.iteration == 3
    assert restored.max_iterations == 8


def test_unpack_state_defaults_when_keys_missing():
    restored = unpack_state({"state": {}})

    assert restored.conversation.messages == []
    assert restored.planner is None
    assert restored.reflection is None
    assert restored.last_node == ""
    assert restored.session_id == ""
    assert restored.iteration == 0
    assert restored.max_iterations == 6
    assert restored.final_answer is None
