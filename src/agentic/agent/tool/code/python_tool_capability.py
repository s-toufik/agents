from typing import Any, Optional, cast

from pydantic import BaseModel

from agentic.agent.tool.schema.tool_result import ToolResult
from agentic.agent.tool.schema.python_tool_input import PythonToolInput
from agentic.infrastructure.code_sandbox.code import CodeFactory, Code, CodeStdout
from agentic.infrastructure.logger.port.logger import Logger
from agentic.infrastructure.code_sandbox.python.adapter import _ALLOWLIST


class PythonToolCapability:
    timeout: int = 10
    max_memory_mb: int = 256

    name: str = "python_executor"
    description: str = f"Execute Python for data analysis or computation. Allowed modules: {', '.join(_ALLOWLIST)}. Assign your final value to `result`. Hard timeout: {timeout}s."
    args_schema: type[BaseModel] = PythonToolInput

    def __init__(self, code_factory: CodeFactory, logger: Optional[Logger] = None) -> None:
        self._code_factory = code_factory
        self._set_logging(logger)

    def _set_logging(self, logger: Logger | None) -> None:
        if logger is None:
            import logging

            self._logger: Logger = cast(Logger, logging.getLogger(__name__))
        else:
            self._logger: Logger = logger

    @classmethod
    def schema(cls) -> dict[str, Any]:
        return {
            "name": cls.name,
            "description": cls.description.format(
                allow_list=", ".join(_ALLOWLIST), timeout=cls.timeout
            ),
            "parameters": cls.args_schema.model_json_schema(),
        }

    async def execute(self, request: PythonToolInput) -> ToolResult:
        call_id: str = request.call_id or ""
        code: str = request.code

        if not code:
            return ToolResult(tool_name=self.name, id=call_id, output="", error="No code provided.")

        code_executor_proc: Code = self._code_factory(
            code=code, code_template=None, code_timeout=self.timeout, max_memory_mb=self.max_memory_mb
        )

        code_result: CodeStdout = await code_executor_proc.execute()

        return ToolResult(
            tool_name=self.name, id=call_id, output=code_result.stdout, error=code_result.stderr
        )
