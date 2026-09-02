from dataclasses import dataclass

from agentic.domain.enum.agent_message_type import AgentMessageType
from agentic.domain.enum.agent_message_status import MessageStreamType


@dataclass(slots=True)
class AgentMessage:
    session_id: str
    content: str
    metadata: dict[str, str] | None
    error: str | None = None
    message_status: MessageStreamType = MessageStreamType.FINAL
    message_type: AgentMessageType = AgentMessageType.TEXT
