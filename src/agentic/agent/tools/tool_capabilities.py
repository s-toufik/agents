from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from agentic.agent.schema.tool_result import ToolResult


class ToolCapability(ABC):

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def args_schema(self) -> type[BaseModel]: ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult: ...