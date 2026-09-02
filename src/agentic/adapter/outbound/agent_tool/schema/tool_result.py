from dataclasses import dataclass


@dataclass
class ToolResult:
    tool_name: str
    id: str
    output: str
    error: str | None = None

    @property
    def content(self) -> str:
        return self.output if not self.error else f"Error: {self.error}"
