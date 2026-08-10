from dataclasses import dataclass
from typing import Optional

from agentic.domain.enum.agent_message_type import AgentMessageType
from agentic.domain.enum.agent_message_status import MessageStreamType


@dataclass(slots=True)
class AgentMessage:
    session_id: str
    content: str
    metadata: Optional[dict[str, str]]
    error: Optional[str] = None
    message_status: MessageStreamType = MessageStreamType.FINAL
    message_type: AgentMessageType = AgentMessageType.TEXT
