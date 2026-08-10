from pydantic import BaseModel

from agentic.domain.enum.agent_message_status import MessageStreamType


class AgentMessageStreamSchema(BaseModel):
    type: MessageStreamType
    content: str

    def serialize(self) -> bytes:
        return (
            f"event_type: {self.type.value}\n"
            f"content: {self.content}\n"
        ).encode("utf-8")