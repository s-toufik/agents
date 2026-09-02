from langchain_core.messages import trim_messages, BaseMessage

from agentic.adapter.outbound.agent.graph.node.node import Node
from agentic.adapter.outbound.agent.graph.schema.agent_state import AgentState
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.graph_state import GraphState
from agentic.adapter.outbound.agent.service.tokens_service import count_message_tokens


class MemoryNode(Node):
    def __init__(self, max_context_tokens: int = 8_000) -> None:
        self._max_context_tokens = max_context_tokens

    async def __call__(self, state: GraphState) -> GraphState:

        state: AgentState = self._unpack(state)
        lc_messages: list[BaseMessage] = state.conversation.to_langchain()

        trimmed: list[BaseMessage] = trim_messages(
            lc_messages,
            token_counter=count_message_tokens,
            max_tokens=self._max_context_tokens,
            strategy="last",
            include_system=False,
        )

        state.conversation = Conversation.from_langchain(trimmed)
        state.last_node = "memory"
        return self._pack(state)
