from typing import Optional

from pydantic import BaseModel


class ToolResult(BaseModel):

    id: str
    output: str
    error: Optional[str] = None

    @property
    def content(self) -> str:
        return self.output if self.error is None else f"Error: {self.error}"
