from agentic.agent.enum.role import Role
from agentic.agent.graph.node import Node
from agentic.agent.schema.conversation_message import ConversationMessage
from agentic.agent.schema.graph_state import GraphState


class FeedbackNode(Node):

    async def __call__(self, gs: GraphState) -> GraphState:
        state = self._unpack(gs)

        critique = (
            state.reflection.critique
            if state.reflection
            else "No specific critique provided."
        )

        state.conversation.append(ConversationMessage(
            role=Role.USER,
            content=(
                f"Your previous answer was not satisfactory.\n"
                f"Critique: {critique}\n\n"
                f"Please try again, addressing the critique above."
            ),
        ))
        state.last_node = "feedback"
        return self._pack(state)