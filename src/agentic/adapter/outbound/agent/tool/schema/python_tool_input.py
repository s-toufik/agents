from pydantic import Field

from agentic.adapter.outbound.agent.tool.schema.tool_input import ToolInput


class PythonToolInput(ToolInput):
    code: str = Field(..., description="Python source code to run in a sandbox.")
