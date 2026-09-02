from pycraftcore.runtime.adapter.python.adapter import PYTHON_ALLOWLIST

from agentic.adapter.outbound.agent_tool.schema.python_tool_input import PythonToolInput

name: str = "python_executor"
timeout: int = 100
max_memory_mb: int = 256
max_concurrency: int = 8
description: str = (
    f"Execute Python code for data analysis or computation"
    f"Allowed modules: {', '.join(PYTHON_ALLOWLIST)}"
    f"You must return the required arguments"
    f"Assign your final value to 'result' if returning result is not relevant set result='no return'."
    f"Hard timeout: {timeout} seconds"
)
args_schema: type[PythonToolInput] = PythonToolInput
