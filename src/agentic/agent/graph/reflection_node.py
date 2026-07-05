from typing import Any

from langchain_core.messages import SystemMessage
from agentic.agent.graph.node import Node
from agentic.agent.schema.graph_state import GraphState
from agentic.agent.schema.reflection_decision import ReflectionDecision


class ReflectionNode(Node):

    _SYSTEM = (
        "You are a self-correction evaluator. "
        "Assess the assistant's last response for correctness and completeness. "
        "Return action='accept' if satisfactory, 'retry' if improvement is needed."
    )

    def __init__(self, llm: Any) -> None:
        self._llm    = llm.with_structured_output(ReflectionDecision)
        self._system = SystemMessage(content=self._SYSTEM)

    async def __call__(self, gs: GraphState) -> GraphState:
        from langchain_core.messages import HumanMessage

        state = self._unpack(gs)

        last = state.conversation.last_assistant()
        answer = last.content if last else "(no assistant answer found)"

        decision: ReflectionDecision = await self._llm.ainvoke([
            self._system,
            HumanMessage(content=f"Evaluate this answer:\n\n{answer}"),
        ])

        state.reflection = decision
        state.last_node  = "reflection"
        return self._pack(state)