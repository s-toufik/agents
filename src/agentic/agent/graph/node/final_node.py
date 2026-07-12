from agentic.agent.graph.node.node import Node
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.graph.schema.graph_state import GraphState


class FinalNode(Node):
    async def __call__(self, graph_state: GraphState) -> GraphState:
        state: AgentState = self._unpack(graph_state)

        last: ConversationMessage | None = state.conversation.last_assistant()
        state.final_answer = last.content if last else "No answer was produced."
        state.last_node = "final"
        return self._pack(state)
