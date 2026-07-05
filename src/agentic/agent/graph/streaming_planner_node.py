import uuid
from typing import Any, Optional

from langchain_core.messages import SystemMessage, AIMessage

from agentic.agent.enum.role import Role
from agentic.agent.graph.node import Node
from agentic.agent.graph.planner_node import PlannerNode
from agentic.agent.schema.conversation_message import ConversationMessage
from agentic.agent.schema.graph_state import GraphState
from agentic.agent.schema.planner_decision import PlannerDecision
from agentic.agent.schema.tool_call import ToolCall
from agentic.agent.tools.tool_registery import ToolRegistry

class StreamingPlannerNode(Node):

    _SYSTEM = PlannerNode._SYSTEM

    def __init__(
        self,
        llm: Any,
        registry: ToolRegistry,
        on_token: Optional[Any] = None,  # async callable(str) -> None
    ) -> None:
        from langchain_core.messages import SystemMessage
        self._llm      = llm
        self._on_token = on_token
        self._system   = SystemMessage(
            content=self._SYSTEM.format(tools=registry.descriptions())
        )

    async def __call__(self, gs: GraphState) -> GraphState:
        from langchain_core.messages import AIMessage

        state = self._unpack(gs)
        lc_messages = [self._system, *state.conversation.to_langchain()]

        chunks: list[Any] = []
        async for chunk in self._llm.astream(lc_messages):
            chunks.append(chunk)
            if hasattr(chunk, "content") and chunk.content:
                if self._on_token is not None:
                    await self._on_token(chunk.content)

        last: AIMessage = chunks[-1] if chunks else AIMessage(content="")
        raw_tcs = getattr(last, "tool_calls", None) or []

        tool_calls = [
            ToolCall(
                id=f"call_{uuid.uuid4().hex[:8]}",
                name=tc["name"],
                args=tc.get("args", {}),
            )
            for tc in raw_tcs
        ]
        decision = PlannerDecision(
            tool_calls=tool_calls,
            answer=last.content if not raw_tcs else None,
            notes=last.content if raw_tcs else None,
        )

        state.conversation.append(ConversationMessage(
            role=Role.ASSISTANT,
            content=last.content or "",
            tool_calls=tool_calls,
        ))
        state.planner   = decision
        state.iteration += 1
        state.last_node  = "planner"

        return self._pack(state)