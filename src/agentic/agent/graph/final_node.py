from agentic.agent.graph.node import Node
from agentic.agent.schema.graph_state import GraphState


class FinalNode(Node):

    async def __call__(self, gs: GraphState) -> GraphState:
        state = self._unpack(gs)

        last = state.conversation.last_assistant()
        state.final_answer = last.content if last else "No answer was produced."
        state.last_node    = "final"
        return self._pack(state)