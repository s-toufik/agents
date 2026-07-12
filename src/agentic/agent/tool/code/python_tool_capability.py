import asyncio
import os
import tempfile
from typing import Any

from pydantic import BaseModel

from agentic.agent.tool.schema.tool_result import ToolResult
from agentic.agent.tool.schema.python_tool_input import PythonToolInput
from agentic.agent.tool.tool_capabilities import ToolCapability


class PythonToolCapability(ToolCapability):
    _TIMEOUT: int = 10
    _MAX_OUTPUT: int = 4_000

    @property
    def name(self) -> str:
        return "python_executor"

    @property
    def description(self) -> str:
        return "Execute Python code in a sandboxed subprocess. Returns stdout."

    @property
    def args_schema(self) -> type[BaseModel]:
        return PythonToolInput

    @classmethod
    def schema(cls) -> dict[str, Any]:
        return {"name": cls.name, "description": cls.description, "parameters": cls.args_schema}

    async def execute(self, **kwargs: Any) -> ToolResult:
        call_id: str = kwargs.pop("_call_id", "")
        code: str = kwargs.get("", "").strip()

        if not code:
            return ToolResult(id=call_id, output="", error="No code provided.")

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            try:
                proc = await asyncio.create_subprocess_exec(
                    "python3",
                    tmp_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self._TIMEOUT)
            except asyncio.TimeoutError:
                return ToolResult(
                    id=call_id, output="", error=f"Execution timed out after {self._TIMEOUT}s."
                )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            return ToolResult(id=call_id, output="", error=err or "Non-zero exit code.")

        output = (out + (f"\nSTDERR:\n{err}" if err else "") or "(no output)")[: self._MAX_OUTPUT]
        return ToolResult(id=call_id, output=output)
