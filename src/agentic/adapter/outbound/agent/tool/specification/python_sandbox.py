from pydantic import BaseModel

from agentic.adapter.outbound.agent.tool.schema.python_tool_input import PythonToolInput
from agentic_core.infrastructure.runtime.python.adapter import ALLOWLIST

name: str = "python_executor"
timeout: int = 100
max_memory_mb: int = 256
max_concurrency: int = 8
description: str = (
    f"Execute Python code for data analysis or computation"
    f"Allowed modules: {', '.join(ALLOWLIST)}"
    f"You must return the required arguments"
    f"Assign your final value to 'result' if returning result is not relevant set result='no return'."
    f"Hard timeout: {timeout} seconds"
)
args_schema: type[BaseModel] = PythonToolInput
