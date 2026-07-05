from typing import Any

from langgraph.graph import END, StateGraph

from agentic.agent.graph.execution_node import ExecutorNode
from agentic.agent.graph.feedback_node import FeedbackNode
from agentic.agent.graph.final_node import FinalNode
from agentic.agent.graph.memory_node import MemoryNode
from agentic.agent.graph.planner_node import PlannerNode
from agentic.agent.graph.reflection_node import ReflectionNode
from agentic.agent.graph.router_node import RouterNode
from agentic.agent.graph.streaming_planner_node import StreamingPlannerNode
from agentic.agent.schema.graph_state import GraphState


class AgentGraph:

    def __init__(
        self,
        planner:    PlannerNode | StreamingPlannerNode,
        router:     RouterNode,
        executor:   ExecutorNode,
        memory:     MemoryNode,
        reflection: ReflectionNode,
        feedback:   FeedbackNode,
        final:      FinalNode,
    ) -> None:
        self._planner    = planner
        self._router     = router
        self._executor   = executor
        self._memory     = memory
        self._reflection = reflection
        self._feedback   = feedback
        self._final      = final

    def build(self, checkpointer: Any = None) -> Any:

        graph = StateGraph(GraphState)

        graph.add_node("planner",    self._planner)
        graph.add_node("executor",   self._executor)
        graph.add_node("memory",     self._memory)
        graph.add_node("reflection", self._reflection)
        graph.add_node("feedback",   self._feedback)
        graph.add_node("final",      self._final)

        graph.set_entry_point("planner")

        _targets = {
            "planner":    "planner",
            "executor":   "executor",
            "reflection": "reflection",
            "feedback":   "feedback",
            "final":      "final",
        }

        # Single RouterNode instance handles all conditional branching
        graph.add_conditional_edges("planner",    self._router, _targets)
        graph.add_conditional_edges("memory",     self._router, _targets)
        graph.add_conditional_edges("reflection", self._router, _targets)
        graph.add_conditional_edges("feedback",   self._router, _targets)

        graph.add_edge("executor", "memory")
        graph.add_edge("final",    END)

        return graph.compile(checkpointer=checkpointer)