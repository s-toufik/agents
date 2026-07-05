from agentic.agent.graph.node import Node
from agentic.agent.schema.conversation import Conversation
from agentic.agent.schema.graph_state import GraphState
from agentic.agent.service.tokens_service import count_message_tokens


class MemoryNode(Node):

    def __init__(self, max_tokens: int = 8_000) -> None:
        self._max_tokens = max_tokens

    async def __call__(self, gs: GraphState) -> GraphState:
        from langchain_core.messages import trim_messages

        state = self._unpack(gs)
        lc_messages = state.conversation.to_langchain()

        trimmed = trim_messages(
            lc_messages,
            token_counter=count_message_tokens,
            max_tokens=self._max_tokens,
            strategy="last",
            include_system=True,
            start_on="human",
        )

        state.conversation = Conversation.from_langchain(trimmed)
        state.last_node    = "memory"
        return self._pack(state)