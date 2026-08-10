from dataclasses import dataclass
from typing import Optional

from agentic.domain.enum.agent_message_status import MessageStreamType


@dataclass(slots=True)
class AgentMessageStream:
    type: MessageStreamType
    content: str
    metadata: Optional[dict[str, str | int | float]] = None
