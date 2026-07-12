from typing import Any

from langgraph.graph import END, StateGraph

from agentic.agent.graph.node.execution_node import ExecutorNode
from agentic.agent.graph.node.feedback_node import FeedbackNode
from agentic.agent.graph.node.final_node import FinalNode
from agentic.agent.graph.node.memory_node import MemoryNode
from agentic.agent.graph.node.planner_node import PlannerNode
from agentic.agent.graph.node.reflection_node import ReflectionNode
from agentic.agent.graph.node.router_node import RouterNode
from agentic.agent.graph.node.streaming_planner_node import StreamingPlannerNode
from agentic.agent.graph.schema.graph_state import GraphState


class AgentGraph:
    def __init__(
        self,
        planner: PlannerNode | StreamingPlannerNode,
        router: RouterNode,
        executor: ExecutorNode,
        memory: MemoryNode,
        reflection: ReflectionNode,
        feedback: FeedbackNode,
        final: FinalNode,
    ) -> None:
        self._planner = planner
        self._router = router
        self._executor = executor
        self._memory = memory
        self._reflection = reflection
        self._feedback = feedback
        self._final = final

    def build(self, checkpointer: Any = None) -> Any:
        graph = StateGraph(GraphState)
        graph.add_node("planner", self._planner)
        graph.add_node("executor", self._executor)
        graph.add_node("memory", self._memory)
        graph.add_node("memory_pre_reflection", self._memory)  # same instance, second entry point
        graph.add_node("reflection", self._reflection)
        graph.add_node("feedback", self._feedback)
        graph.add_node("final", self._final)

        graph.set_entry_point("memory")

        # Only planner and reflection still need runtime branching.
        planner_targets = {
            "executor": "executor",
            "reflection": "memory_pre_reflection",  # planner's "no tool" branch
            "final": "final",
        }
        reflection_targets = {
            "feedback": "feedback",
            "final": "final",
        }

        graph.add_conditional_edges("planner", self._router, planner_targets)
        graph.add_conditional_edges("reflection", self._router, reflection_targets)

        # Deterministic: every path into memory has a fixed destination.
        graph.add_edge("memory", "planner")
        graph.add_edge("memory_pre_reflection", "reflection")
        graph.add_edge("executor", "memory")
        graph.add_edge("feedback", "memory")
        graph.add_edge("final", END)

        return graph.compile(checkpointer=checkpointer)
