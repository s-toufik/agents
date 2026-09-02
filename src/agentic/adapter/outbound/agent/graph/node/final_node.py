from agentic.adapter.outbound.agent.graph.node.node import Node
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState


class FinalNode(Node):
    async def __call__(self, state: GraphState) -> GraphState:
        state: AgentState = self._unpack(state)

        last: ConversationMessage | None = state.conversation.last_assistant()
        state.final_answer = last.content if last else "No answer was produced."
        state.last_node = "final"
        return self._pack(state)
