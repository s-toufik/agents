from typing import Any, Optional, Mapping, Callable, TypeVar, Protocol, Type

from agentic.agent.graph.schema.conversation_message import ConversationMessage
from agentic.agent.enum.role import Role
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)

from agentic.agent.graph.schema.tool_call import ToolCall

T = TypeVar("T")


class Handler(Protocol[T]):
    def __call__(self, __msg: T) -> ConversationMessage: ...


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
        return [self.to_langchain_dispatcher[message.role](message) for message in self.messages]

    @property
    def to_langchain_dispatcher(
        self,
    ) -> Mapping[Role, Callable[[ConversationMessage], BaseMessage]]:
        return {
            Role.USER: self._to_human,
            Role.ASSISTANT: self._to_assistant,
            Role.TOOL: self._to_tool,
            Role.SYSTEM: self._to_system,
        }

    @classmethod
    def from_langchain(cls, lc_messages: list[Any]) -> "Conversation":
        messages: list[ConversationMessage] = [
            cls().from_langchain_dispatcher[type(message)](message) for message in lc_messages
        ]
        return cls(messages)

    @property
    def from_langchain_dispatcher(self) -> Mapping[Type[BaseMessage], Handler[BaseMessage]]:
        return {
            HumanMessage: self._from_human,
            AIMessage: self._from_assistant,
            ToolMessage: self._from_tool,
            SystemMessage: self._from_system,
        }

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

    @staticmethod
    def _from_system(message: SystemMessage) -> ConversationMessage:
        return ConversationMessage(role=Role.SYSTEM, content=str(message.content) or "")

    @staticmethod
    def _from_tool(message: ToolMessage) -> ConversationMessage:
        return ConversationMessage(
            role=Role.TOOL,
            content=str(message.content) or "",
            tool_call_id=message.tool_call_id,
        )

    @staticmethod
    def _from_assistant(message: AIMessage) -> ConversationMessage:
        return ConversationMessage(
            role=Role.ASSISTANT,
            content=str(message.content) or "",
            tool_calls=[
                ToolCall(
                    id=tool_call_["id"], name=tool_call_["name"], args=tool_call_.get("args", {})
                )
                for tool_call_ in (message.tool_calls or [])
            ],
        )

    @staticmethod
    def _from_human(message: HumanMessage) -> ConversationMessage:
        return ConversationMessage(role=Role.USER, content=str(message.content) or "")
