from typing import Any

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state
from agentic.domain.enum.agent_message_status import AgentMessageStatus
from agentic.domain.model.agent_message import AgentMessage
from agentic.domain.model.agent_request import AgentRequest


class LangAgent:
    def __init__(self, graphs: dict[str, Any]) -> None:
        self._graphs = graphs

    async def run(self, request: AgentRequest) -> AgentMessage:
        graph = self._graphs[request.model_name]
        config = {"configurable": {"thread_id": request.request_id}}

        state = await self._load_state(graph, config, request.request_id)
        self._append_user_message(state, request.message)

        result: GraphState = await graph.ainvoke(pack_state(state))
        final_state: AgentState = unpack_state(result)

        return AgentMessage(
            content=final_state.final_answer or "",
            error=None,
            metadata=None,
            message_status=AgentMessageStatus.END,
        )

    @staticmethod
    async def _load_state(graph: Any, config: dict, session_id: str) -> AgentState:
        snapshot = await graph.aget_state(config)
        if snapshot.values:
            return unpack_state(snapshot.values)
        return AgentState(session_id=session_id)

    @staticmethod
    def _append_user_message(state: AgentState, message: str) -> None:
        state.iteration = 0
        state.conversation.append(ConversationMessage(role=Role.USER, content=message))
