from typing import Any

from agentic.agent.graph.agent_graph import AgentGraph
from agentic.agent.graph.execution_node import ExecutorNode
from agentic.agent.graph.feedback_node import FeedbackNode
from agentic.agent.graph.final_node import FinalNode
from agentic.agent.graph.memory_node import MemoryNode
from agentic.agent.graph.planner_node import PlannerNode
from agentic.agent.graph.reflection_node import ReflectionNode
from agentic.agent.graph.router_node import RouterNode
from agentic.agent.graph.streaming_planner_node import StreamingPlannerNode
from agentic.agent.schema.agent_state import AgentState
from agentic.agent.schema.graph_state import GraphState
from agentic.agent.service.state_serialization import _pack
from agentic.agent.tools.python_tool_capability import PythonToolCapability
from agentic.agent.tools.sql_tool_capability import SQLToolCapability
from agentic.agent.tools.tool_registery import ToolRegistry


def build_agent(
    llm: Any,
    database: Any,
    sql_dialect:    str  = "oracle",
    max_tokens:     int  = 8_000,
    max_iterations: int  = 6,
    use_streaming:  bool = False,
    checkpointer:   Any  = None
) -> tuple[Any, GraphState]:

    registry = ToolRegistry([
        SQLToolCapability(database, default_dialect=sql_dialect),
        PythonToolCapability(),
    ])

    planner: PlannerNode | StreamingPlannerNode = (
        StreamingPlannerNode(llm, registry)
        if use_streaming
        else PlannerNode(llm, registry)
    )

    graph = AgentGraph(
        planner=planner,
        router=RouterNode(),
        executor=ExecutorNode(registry),
        memory=MemoryNode(max_tokens=max_tokens),
        reflection=ReflectionNode(llm),
        feedback=FeedbackNode(),
        final=FinalNode(),
    ).build(checkpointer=checkpointer)

    initial_state = AgentState(max_iterations=max_iterations)
    return graph, _pack(initial_state)