from pydantic import BaseModel

from agentic.domain.enum.agent_message_status import MessageStreamType
from agentic.domain.enum.agent_message_type import AgentMessageType


class AgentMessageSchema(BaseModel):
    session_id: str
    content: str
    metadata: dict[str, str | int | float] | None
    error: str | None = None
    message_status: MessageStreamType = MessageStreamType.FINAL
    message_type: AgentMessageType = AgentMessageType.TEXT

    def serialize(self) -> bytes:
        return (
            f"event_type: {self.message_status.value}\n"
            f"session_id: {self.session_id}\n"
            f"content: {self.content}\n"
            f"metadata: {self.metadata}\n"
            f"error: {self.error}\n"
            f"message_status: {self.message_status.value}\n"
            f"message_type: {self.message_type.value}\n"
        ).encode()
