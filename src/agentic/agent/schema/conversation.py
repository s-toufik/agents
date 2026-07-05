from typing import Any, Optional

from agentic.agent.schema.conversation_message import ConversationMessage
from agentic.agent.enum.role import Role
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from agentic.agent.schema.tool_call import ToolCall


class Conversation:

    def __init__(self, messages: list[ConversationMessage] | None = None) -> None:
        self.messages: list[ConversationMessage] = messages or []

    def append(self, msg: ConversationMessage) -> None:
        self.messages.append(msg)

    def last(self) -> Optional[ConversationMessage]:
        return self.messages[-1] if self.messages else None

    def last_assistant(self) -> Optional[ConversationMessage]:
        for msg in reversed(self.messages):
            if msg.role == Role.ASSISTANT:
                return msg
        return None

    def copy(self) -> "Conversation":
        return Conversation(list(self.messages))

    def to_langchain(self) -> list[Any]:


        out: list[Any] = []
        for m in self.messages:
            if m.role == Role.USER:
                out.append(HumanMessage(content=m.content))

            elif m.role == Role.ASSISTANT:
                lc_tool_calls = [
                    {"id": tc.id, "name": tc.name, "args": tc.args}
                    for tc in m.tool_calls
                ]
                out.append(AIMessage(content=m.content, tool_calls=lc_tool_calls))

            elif m.role == Role.TOOL:
                out.append(
                    ToolMessage(
                        content=m.content,
                        tool_call_id=m.tool_call_id or "",
                    )
                )
            else:
                out.append(SystemMessage(content=m.content))
        return out

    @classmethod
    def from_langchain(cls, lc_messages: list[Any]) -> "Conversation":
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        msgs: list[ConversationMessage] = []
        for m in lc_messages:
            if isinstance(m, HumanMessage):
                msgs.append(ConversationMessage(role=Role.USER, content=m.content or ""))
            elif isinstance(m, AIMessage):
                tcs = [
                    ToolCall(id=tc["id"], name=tc["name"], args=tc.get("args", {}))
                    for tc in (m.tool_calls or [])
                ]
                msgs.append(ConversationMessage(
                    role=Role.ASSISTANT,
                    content=m.content or "",
                    tool_calls=tcs,
                ))
            elif isinstance(m, ToolMessage):
                msgs.append(ConversationMessage(
                    role=Role.TOOL,
                    content=m.content or "",
                    tool_call_id=m.tool_call_id,
                ))
            elif isinstance(m, SystemMessage):
                msgs.append(ConversationMessage(role=Role.SYSTEM, content=m.content or ""))
        return cls(msgs)