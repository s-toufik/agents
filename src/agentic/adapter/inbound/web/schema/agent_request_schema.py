from pydantic import BaseModel

from agentic.domain.model.agent_request import AgentRequest


class AgentRequestSchema(BaseModel):
    message: str
    model_name: str
    request_id: str

    def to_domain(self) -> AgentRequest:
        return AgentRequest(
            message=self.message, model_name=self.model_name, request_id=self.request_id
        )
