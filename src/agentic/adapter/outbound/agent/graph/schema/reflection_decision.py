from pydantic import BaseModel

from agentic.adapter.outbound.agent.enum.reflection_action import ReflectionAction


class ReflectionDecision(BaseModel):
    action: ReflectionAction
    critique: str

    @property
    def should_retry(self) -> bool:
        return self.action == ReflectionAction.RETRY
