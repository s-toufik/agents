from agentic.agent.graph.node import Node


class RouterNode(Node):
    """
    Routing table
    ─────────────
    Iteration cap checked first — always → "final" when exhausted.

    last_node == "planner"
        planner.wants_tools → "executor"
        else                → "reflection"

    last_node == "memory"   → "planner"   (continue tool loop)
    last_node == "feedback" → "planner"   (re-plan with critique)

    last_node == "reflection"
        reflection.should_retry → "feedback"
        else                    → "final"
    """

    async def __call__(self, gs: GraphState) -> str:  # type: ignore[override]
        state = self._unpack(gs)

        if state.iteration >= state.max_iterations:
            return "final"

        match state.last_node:
            case "planner":
                return "executor" if (state.planner and state.planner.wants_tools) else "reflection"
            case "memory" | "feedback":
                return "planner"
            case "reflection":
                return "feedback" if (state.reflection and state.reflection.should_retry) else "final"
            case _:
                return "final"