from typing import Any, Optional, Mapping, Callable

from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.enum.role import Role
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)

from agentic.agent.tool.schema.tool_call import ToolCall


class Conversation:
    def __init__(self, messages: list[ConversationMessage] | None = None) -> None:
        self.messages: list[ConversationMessage] = messages or []

    def append(self, msg: ConversationMessage) -> None:
        self.messages.append(msg)

    def last(self) -> Optional[ConversationMessage]:
        return self.messages[-1] if self.messages else None

    def first_user(self) -> Optional[ConversationMessage]:
        for msg in self.messages:
            if msg.role == Role.USER:
                return msg
        return None

    def last_assistant(self) -> Optional[ConversationMessage]:
        for msg in reversed(self.messages):
            if msg.role == Role.ASSISTANT:
                return msg
        return None

    def copy(self) -> "Conversation":
        return Conversation(list(self.messages))

    def to_langchain(self) -> list[BaseMessage]:
        return [self._TO_LANGCHAIN_DISPATCHER[message.role](message) for message in self.messages]

    @classmethod
    def from_langchain(cls, lc_messages: list[Any]) -> "Conversation":
        messages: list[ConversationMessage] = [
            cls._FROM_LANGCHAIN_DISPATCHER[type(message)](message) for message in lc_messages
        ]
        return cls(messages)

    @staticmethod
    def _to_system(message: ConversationMessage) -> SystemMessage:
        return SystemMessage(content=message.content)

    @staticmethod
    def _to_tool(message: ConversationMessage) -> ToolMessage:
        return ToolMessage(
            content=message.content,
            tool_call_id=message.tool_call_id or "",
        )

    @staticmethod
    def _to_assistant(message: ConversationMessage) -> AIMessage:
        return AIMessage(
            content=message.content,
            tool_calls=[
                {"id": tool_call_.id, "name": tool_call_.name, "args": tool_call_.args}
                for tool_call_ in message.tool_calls
            ],
        )

    @staticmethod
    def _to_human(message: ConversationMessage) -> HumanMessage:
        return HumanMessage(content=message.content)

    _TO_LANGCHAIN_DISPATCHER: Mapping[Role, Callable[[ConversationMessage], BaseMessage]] = {
        Role.USER: _to_human,
        Role.ASSISTANT: _to_assistant,
        Role.TOOL: _to_tool,
        Role.SYSTEM: _to_system,
    }

    @classmethod
    def _from_system(cls, message: SystemMessage) -> ConversationMessage:
        return ConversationMessage(role=Role.SYSTEM, content=message.content.__repr__() or "")

    @classmethod
    def _from_tool(cls, message: ToolMessage) -> ConversationMessage:
        return ConversationMessage(
            role=Role.TOOL,
            content=message.content.__repr__() or "",
            tool_call_id=message.tool_call_id,
        )

    @classmethod
    def _from_assistant(cls, message: AIMessage) -> ConversationMessage:
        return ConversationMessage(
            role=Role.ASSISTANT,
            content=message.content.__repr__() or "",
            tool_calls=[
                ToolCall(
                    id=tool_call_["id"], name=tool_call_["name"], args=tool_call_.get("args", {})
                )
                for tool_call_ in (message.tool_calls or [])
            ],
        )

    @classmethod
    def _from_human(cls, message: HumanMessage) -> ConversationMessage:
        return ConversationMessage(role=Role.USER, content=message.content.__repr__() or "")

    _FROM_LANGCHAIN_DISPATCHER: Mapping[
        BaseMessage, Callable[[BaseMessage], ConversationMessage]
    ] = {
        HumanMessage: _from_human,
        AIMessage: _from_assistant,
        ToolMessage: _from_assistant,
        SystemMessage: _from_system,
    }
