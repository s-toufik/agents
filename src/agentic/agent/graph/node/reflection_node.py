from typing import Any, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from agentic.agent.graph.node.node import Node
from agentic.agent.graph.schema.agent_state import AgentState
from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.graph.schema.graph_state import GraphState
from agentic.agent.graph.schema.reflection_decision import ReflectionDecision
from agentic.agent.service.prompt_service import PromptService


class ReflectionNode(Node):
    def __init__(self, llm: BaseChatModel, prompt_service: PromptService) -> None:
        self._llm = llm
        self._prompt_service = prompt_service

    async def __call__(self, graph_state: GraphState) -> GraphState:

        state: AgentState = self._unpack(graph_state)

        last: ConversationMessage | None = state.conversation.last_assistant()
        answer: str = last.content if last else "(no assistant answer found)"

        lc_messages: list[BaseMessage] = [
            SystemMessage(
                content=self._prompt_service.reflection_system_prompt(
                    ReflectionDecision.model_json_schema()
                )
            ),
            HumanMessage(content=f"Evaluate this answer:\n\n{answer}"),
        ]

        raw: AIMessage
        parsing_status: Exception
        decision: ReflectionDecision
        raw_dict: dict[str, Any] = cast(
            dict[str, Any],
            await self._llm.with_structured_output(ReflectionDecision, include_raw=True).ainvoke(
                lc_messages
            ),
        )
        raw, decision, parsing_status = raw_dict.values()

        state.reflection = decision
        state.last_node = "reflection"
        return self._pack(state)
