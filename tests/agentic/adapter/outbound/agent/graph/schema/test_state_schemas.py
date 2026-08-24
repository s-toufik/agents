from agentic.adapter.outbound.agent.enum.reflection_action import ReflectionAction
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.schema.planner_decision import PlannerDecision
from agentic.adapter.outbound.agent.graph.schema.reflection_decision import ReflectionDecision
from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall


def test_agent_state_defaults():
    state = AgentState()

    assert isinstance(state.conversation, Conversation)
    assert state.conversation.messages == []
    assert state.planner is None
    assert state.reflection is None
    assert state.last_node == ""
    assert state.session_id == ""
    assert state.iteration == 0
    assert state.max_iterations == 20
    assert state.final_answer is None


def test_conversation_message_tool_calls_default_not_shared_across_instances():
    a = ConversationMessage(role=Role.USER, content="a")
    b = ConversationMessage(role=Role.USER, content="b")
    a.tool_calls.append(ToolCall(id="x", name="y"))

    assert a.tool_calls != b.tool_calls
    assert b.tool_calls == []


def test_tool_call_args_default_not_shared_across_instances():
    a = ToolCall(id="1", name="tool")
    b = ToolCall(id="2", name="tool")
    a.args["k"] = "v"

    assert a.args == {"k": "v"}
    assert b.args == {}


def test_planner_decision_wants_tools_true_when_tool_calls_present():
    decision = PlannerDecision(tool_calls=[ToolCall(id="1", name="tool")])

    assert decision.wants_tools is True


def test_planner_decision_wants_tools_false_when_empty():
    decision = PlannerDecision()

    assert decision.wants_tools is False


def test_reflection_decision_should_retry_true_on_retry_action():
    decision = ReflectionDecision(action=ReflectionAction.RETRY, critique="try again")

    assert decision.should_retry is True


def test_reflection_decision_should_retry_false_on_accept_action():
    decision = ReflectionDecision(action=ReflectionAction.ACCEPT, critique="looks good")

    assert decision.should_retry is False
