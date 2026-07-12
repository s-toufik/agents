from agentic.agent.enum.role import Role
from agentic.agent.graph.node.node import Node
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.graph.schema.graph_state import GraphState
from agentic.agent.service.prompt_service import PromptService


class FeedbackNode(Node):
    def __init__(self, prompt_service: PromptService) -> None:
        self._prompt_service = prompt_service

    async def __call__(self, graph_state: GraphState) -> GraphState:
        state: AgentState = self._unpack(graph_state)

        critique: str = (
            state.reflection.critique if state.reflection else "No specific critique provided."
        )

        state.conversation.append(
            ConversationMessage(
                role=Role.USER,
                content=self._prompt_service.feedback_system_prompt(critique),
            )
        )
        state.last_node = "feedback"
        return self._pack(state)
