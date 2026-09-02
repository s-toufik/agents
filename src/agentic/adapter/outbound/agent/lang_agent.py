from typing import Any

from langchain_core.exceptions import ModelError

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState
from agentic.adapter.outbound.agent.service.state_serialization import pack_state, unpack_state
from agentic.application.port.outbound.agent_port import AgentUnavailableError
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

        result: GraphState = await self._invoke(graph, state, config)
        final_state: AgentState = unpack_state(result)

        return AgentMessage(
            session_id=final_state.session_id,
            content=final_state.final_answer or "",
            metadata={
                "iteration": str(final_state.iteration),
                "max_iteration": str(final_state.max_iterations),
            },
        )

    @staticmethod
    async def _invoke(graph: Any, state: AgentState, config: dict) -> GraphState:
        try:
            return await graph.ainvoke(pack_state(state), config=config)
        except ModelError as exception:
            # langchain_core's own provider-agnostic exception hierarchy: every
            # chat-model integration (not just OpenAI) raises subclasses of
            # ModelError for its own SDK errors, each correctly flagged
            # `is_retryable` by condition (connection/timeout/rate-limit/5xx
            # are retryable; auth/permission/invalid-request/not-found aren't).
            # Whatever caused this -- our own circuit breaker rejecting, a real
            # network outage, the provider rate-limiting us -- "retryable"
            # means the same thing to a caller: try again shortly.
            if exception.is_retryable:
                raise AgentUnavailableError(str(exception)) from exception
            raise

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
