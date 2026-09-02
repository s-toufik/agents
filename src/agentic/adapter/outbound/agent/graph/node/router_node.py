from agentic.adapter.outbound.agent.graph.node.node import Node
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState


class RouterNode(Node):
    async def __call__(self, state: GraphState) -> str:

        state: AgentState = self._unpack(state)

        if state.iteration >= state.max_iterations:
            return "final"

        match state.last_node:
            case "planner":
                if state.planner and state.planner.wants_tools:
                    return "executor"
                else:
                    return "reflection"

            case "reflection":
                if state.reflection and state.reflection.should_retry:
                    return "feedback"
                else:
                    return "final"

            case _:
                return "final"
