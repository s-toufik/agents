import uuid
from typing import Any
from langchain_core.messages import SystemMessage

from agentic.agent.enum.role import Role
from agentic.agent.graph.node import Node
from agentic.agent.schema.conversation_message import ConversationMessage
from agentic.agent.schema.graph_state import GraphState
from agentic.agent.schema.planner_decision import PlannerDecision
from agentic.agent.schema.tool_call import ToolCall
from agentic.agent.tools.tool_registery import ToolRegistry


class PlannerNode(Node):

    _SYSTEM = (
        "You are an expert assistant.\n"
        "Available tools:\n"
        "{tools}\n\n"
        "Rules:\n"
        "  - Always fill `notes` with your reasoning first.\n"
        "  - Populate `tool_calls` to use tools, OR `answer` to reply directly.\n"
        "  - Never populate both tool_calls and answer."
    )

    def __init__(self, llm: Any, registry: ToolRegistry) -> None:
        self._llm = llm.with_structured_output(PlannerDecision)
        self._system = SystemMessage(
            content=self._SYSTEM.format(tools=registry.descriptions())
        )

    async def __call__(self, gs: GraphState) -> GraphState:
        state = self._unpack(gs)

        lc_messages = [self._system, *state.conversation.to_langchain()]
        decision: PlannerDecision = await self._llm.ainvoke(lc_messages)

        # Assign stable UUIDs to tool calls
        tool_calls = [
            ToolCall(
                id=f"call_{uuid.uuid4().hex[:8]}",
                name=tc.name,
                args=tc.args,
            )
            for tc in decision.tool_calls
        ]
        decision = PlannerDecision(
            tool_calls=tool_calls,
            answer=decision.answer,
            notes=decision.notes,
        )

        state.conversation.append(ConversationMessage(
            role=Role.ASSISTANT,
            content=decision.answer or decision.notes or "",
            tool_calls=tool_calls,
        ))
        state.planner   = decision
        state.iteration += 1
        state.last_node  = "planner"

        return self._pack(state)