import pytest

from agentic.adapter.outbound.agent.graph.node.router_node import RouterNode
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.planner_decision import PlannerDecision
from agentic.adapter.outbound.agent.graph.schema.reflection_decision import ReflectionDecision
from agentic.adapter.outbound.agent.enum.reflection_action import ReflectionAction
from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall
from agentic.adapter.outbound.agent.service.state_serialization import pack_state


@pytest.mark.asyncio
async def test_iteration_at_max_routes_to_final_regardless_of_last_node():
    state = AgentState(iteration=5, max_iterations=5, last_node="planner")

    result = await RouterNode()(pack_state(state))

    assert result == "final"


@pytest.mark.asyncio
async def test_planner_with_tool_calls_routes_to_executor():
    state = AgentState(
        last_node="planner",
        planner=PlannerDecision(tool_calls=[ToolCall(id="1", name="tool")]),
    )

    result = await RouterNode()(pack_state(state))

    assert result == "executor"


@pytest.mark.asyncio
async def test_planner_without_tool_calls_routes_to_reflection():
    state = AgentState(last_node="planner", planner=PlannerDecision())

    result = await RouterNode()(pack_state(state))

    assert result == "reflection"


@pytest.mark.asyncio
async def test_reflection_should_retry_routes_to_feedback():
    state = AgentState(
        last_node="reflection",
        reflection=ReflectionDecision(action=ReflectionAction.RETRY, critique="retry"),
    )

    result = await RouterNode()(pack_state(state))

    assert result == "feedback"


@pytest.mark.asyncio
async def test_reflection_accept_routes_to_final():
    state = AgentState(
        last_node="reflection",
        reflection=ReflectionDecision(action=ReflectionAction.ACCEPT, critique="good"),
    )

    result = await RouterNode()(pack_state(state))

    assert result == "final"


@pytest.mark.asyncio
async def test_unknown_last_node_routes_to_final():
    state = AgentState(last_node="memory")

    result = await RouterNode()(pack_state(state))

    assert result == "final"
