from typing import Any, Optional

from agentic.agent.graph.agent_graph import AgentGraph
from agentic.agent.graph.node.execution_node import ExecutorNode
from agentic.agent.graph.node.feedback_node import FeedbackNode
from agentic.agent.graph.node.final_node import FinalNode
from agentic.agent.graph.node.memory_node import MemoryNode
from agentic.agent.graph.node.planner_node import PlannerNode
from agentic.agent.graph.node.reflection_node import ReflectionNode
from agentic.agent.graph.node.router_node import RouterNode
from agentic.agent.graph.node.streaming_planner_node import StreamingPlannerNode
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.graph_state import GraphState
from agentic.agent.service.prompt_service import PromptService
from agentic.agent.service.state_serialization import _pack
from agentic.agent.tool.code.python_tool_capability import PythonToolCapability
from agentic.agent.tool.sql.sql_tool_capability import SQLToolCapability
from agentic.agent.tool.tool_registery import ToolRegistry


def build_agent(
    llm: Any,
    database: Any,
    sql_dialect: str = "oracle",
    max_tokens: int = 8_000,
    max_iterations: int = 6,
    use_streaming: bool = False,
    on_token: Optional[Any] = None,
    checkpointer: Any = None,
) -> tuple[Any, GraphState]:

    registry = ToolRegistry(
        [
            SQLToolCapability(database, default_dialect=sql_dialect),
            PythonToolCapability(),
        ]
    )

    planner: PlannerNode | StreamingPlannerNode = (
        StreamingPlannerNode(llm, registry, PromptService(), on_token)
        if use_streaming
        else PlannerNode(llm, registry, PromptService())
    )

    graph = AgentGraph(
        planner=planner,
        router=RouterNode(),
        executor=ExecutorNode(registry),
        memory=MemoryNode(max_tokens=max_tokens),
        reflection=ReflectionNode(llm, PromptService()),
        feedback=FeedbackNode(PromptService()),
        final=FinalNode(),
    ).build(checkpointer=checkpointer)

    initial_state = AgentState(max_iterations=max_iterations)
    return graph, _pack(initial_state)
