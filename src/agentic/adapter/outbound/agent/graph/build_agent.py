from typing import Any

from agentic.adapter.outbound.agent.graph.agent_graph import AgentGraph
from agentic.adapter.outbound.agent.graph.node.execution_node import ExecutorNode
from agentic.adapter.outbound.agent.graph.node.feedback_node import FeedbackNode
from agentic.adapter.outbound.agent.graph.node.final_node import FinalNode
from agentic.adapter.outbound.agent.graph.node.memory_node import MemoryNode
from agentic.adapter.outbound.agent.graph.node.planner_node import PlannerNode
from agentic.adapter.outbound.agent.graph.node.reflection_node import ReflectionNode
from agentic.adapter.outbound.agent.graph.node.router_node import RouterNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState
from agentic.adapter.outbound.agent.service.prompt_service import PromptService
from agentic.adapter.outbound.agent.service.state_serialization import pack_state
from agentic.adapter.outbound.agent.tool.tool_registery import ToolRegistry


def build_agent(
    planner_llm: Any,
    reflection_llm: Any,
    tool_registry: ToolRegistry,
    max_tokens: int = 8_000,
    max_iterations: int = 6,
    use_streaming: bool = False,
    on_token: Any | None = None,
    checkpointer: Any = None,
) -> tuple[Any, GraphState]:

    planner = PlannerNode(
        llm=planner_llm,
        tool_registry=tool_registry,
        prompt_service=PromptService(),
        on_token=on_token if use_streaming else None,
    )

    graph = AgentGraph(
        planner=planner,
        router=RouterNode(),
        executor=ExecutorNode(tool_registry),
        memory=MemoryNode(max_tokens=max_tokens),
        reflection=ReflectionNode(reflection_llm, PromptService()),
        feedback=FeedbackNode(PromptService()),
        final=FinalNode(),
    ).build(checkpointer=checkpointer)

    initial_state = AgentState(max_iterations=max_iterations)
    return graph, pack_state(initial_state)
