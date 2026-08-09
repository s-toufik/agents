from dataclasses import dataclass
from typing import Optional

from agentic.domain.enum.agent_message_type import AgentMessageType
from agentic.domain.enum.agent_message_status import AgentMessageStatus


@dataclass(slots=True)
class AgentMessage:
    content: str
    error: Optional[str]
    metadata: Optional[dict[str, str]]
    message_status: AgentMessageStatus
    message_type: AgentMessageType = AgentMessageType.TEXT
