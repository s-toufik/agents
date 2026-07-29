import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, AIMessage, BaseMessage

from agentic.agent.enum.role import Role
from agentic.agent.graph.node.node import Node
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.graph.schema.graph_state import GraphState
from agentic.agent.graph.schema.planner_decision import PlannerDecision
from agentic.agent.service.prompt_service import PromptService
from agentic.agent.graph.schema.tool_call import ToolCall
from agentic.agent.tool.tool_registery import ToolRegistry


class PlannerNode(Node):
    def __init__(
        self, llm: BaseChatModel, tool_registry: ToolRegistry, prompt_service: PromptService
    ) -> None:
        self._llm = llm
        self._tool_registry = tool_registry
        self._prompt_service = prompt_service

    async def __call__(self, graph_state: GraphState) -> GraphState:
        state: AgentState = self._unpack(graph_state)

        lc_messages: list[BaseMessage] = [
            SystemMessage(content=self._prompt_service.planner_system_prompt()),
            *state.conversation.to_langchain(),
        ]

        raw: AIMessage = await self._llm.bind_tools(self._tool_registry.descriptions()).ainvoke(
            lc_messages
        )

        tool_calls: list[ToolCall] = [
            ToolCall(
                id=f"call_{uuid.uuid4().hex[:8]}",
                name=tool_call.get("name"),
                args=tool_call.get("args", {}),
            )
            for tool_call in raw.tool_calls
        ]

        decision: PlannerDecision = PlannerDecision(
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
