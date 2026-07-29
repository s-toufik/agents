from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolResult:
    tool_name: str
    id: str
    output: str
    error: Optional[str] = None

    @property
    def content(self) -> str:
        return self.output if not self.error else f"Error: {self.error}"
