from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolResult:
    id: str
    output: str
    error: Optional[str] = None

    @property
    def content(self) -> str:
        return self.output if self.error is None else f"Error: {self.error}"
