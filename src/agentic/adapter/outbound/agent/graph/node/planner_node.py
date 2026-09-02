import uuid
from collections.abc import Awaitable, Callable
from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, SystemMessage

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.node.node import Node
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState
from agentic.adapter.outbound.agent.graph.schema.planner_decision import PlannerDecision
from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall
from agentic.adapter.outbound.agent.service.prompt_service import PromptService
from agentic.adapter.outbound.agent_tool.tool_registery import ToolRegistry


class PlannerNode(Node):
    def __init__(
        self,
        llm: BaseChatModel,
        tool_registry: ToolRegistry,
        prompt_service: PromptService,
        on_token: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        self._llm = llm
        self._tool_registry = tool_registry
        self._prompt_service = prompt_service
        self._on_token = on_token

    async def __call__(self, state: GraphState) -> GraphState:
        state: AgentState = self._unpack(state)

        lc_messages: list[BaseMessage] = [
            SystemMessage(content=self._prompt_service.planner_system_prompt()),
            *state.conversation.to_langchain(),
        ]
        on_token = self._on_token
        bound_llm = self._llm.bind_tools(self._tool_registry.descriptions())
        raw: AIMessage | AIMessageChunk = (
            await self._stream(bound_llm, lc_messages, on_token)
            if on_token is not None
            else await bound_llm.ainvoke(lc_messages)
        )

        tool_calls: list[ToolCall] = [
            ToolCall(
                id=f"call_{uuid.uuid4().hex[:8]}",
                name=tool_call.get("name"),
                args=tool_call.get("args", {}),
            )
            for tool_call in raw.tool_calls
        ]

        decision = PlannerDecision(
            tool_calls=tool_calls, answer=str(raw.content) if not raw.tool_calls else None
        )

        state.conversation.append(
            ConversationMessage(
                role=Role.ASSISTANT,
                content=decision.answer or "",
                tool_calls=tool_calls,
            )
        )
        state.planner = decision
        state.iteration += 1
        state.last_node = "planner"

        return self._pack(state)

    @staticmethod
    async def _stream(
        bound_llm, lc_messages: list[BaseMessage], on_token: Callable[[str], Awaitable[None]]
    ) -> AIMessageChunk:
        raw: AIMessageChunk = AIMessageChunk(content="")
        async for chunk in bound_llm.astream(lc_messages):
            raw = cast(AIMessageChunk, raw + chunk)
            if chunk.content:
                await on_token(chunk.content)
        return raw
