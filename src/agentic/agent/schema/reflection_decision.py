from pydantic import BaseModel

from agentic.agent.enum.reflection_action import ReflectionAction


class ReflectionDecision(BaseModel):
    action: ReflectionAction
    critique: str

    @property
    def should_retry(self) -> bool:
        return self.action == ReflectionAction.RETRY