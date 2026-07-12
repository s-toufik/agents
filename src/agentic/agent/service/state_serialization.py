from agentic.agent.enum.role import Role
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation import Conversation
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.graph.schema.graph_state import GraphState
from agentic.agent.graph.schema.planner_decision import PlannerDecision
from agentic.agent.graph.schema.reflection_decision import ReflectionDecision
from agentic.agent.tool.schema.tool_call import ToolCall


def _pack(state: AgentState) -> GraphState:
    """Serialise AgentState → GraphState for LangGraph."""

    def ser_conv(conversation: Conversation) -> list[dict]:
        return [
            {
                "role": message.role.value,
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls],
                "tool_call_id": message.tool_call_id,
            }
            for message in conversation.messages
        ]

    return {
        "state": {
            "conversation": ser_conv(state.conversation),
            "planner": state.planner.model_dump() if state.planner else None,
            "reflection": state.reflection.model_dump() if state.reflection else None,
            "last_node": state.last_node,
            "session_id": state.session_id,
            "iteration": state.iteration,
            "max_iterations": state.max_iterations,
            "final_answer": state.final_answer,
        }
    }


def _unpack(graph_state: GraphState) -> AgentState:
    """Deserialise GraphState → AgentState."""
    _graph_state = graph_state["state"]

    conversation = Conversation(
        [
            ConversationMessage(
                role=Role(message["role"]),
                content=message["content"],
                tool_calls=[ToolCall(**tc) for tc in (message.get("tool_calls") or [])],
                tool_call_id=message.get("tool_call_id"),
            )
            for message in (_graph_state.get("conversation") or [])
        ]
    )

    return AgentState(
        conversation=conversation,
        planner=PlannerDecision(**_graph_state["planner"]) if _graph_state.get("planner") else None,
        reflection=ReflectionDecision(**_graph_state["reflection"])
        if _graph_state.get("reflection")
        else None,
        last_node=_graph_state.get("last_node", ""),
        session_id=_graph_state.get("session_id", ""),
        iteration=_graph_state.get("iteration", 0),
        max_iterations=_graph_state.get("max_iterations", 6),
        final_answer=_graph_state.get("final_answer"),
    )
