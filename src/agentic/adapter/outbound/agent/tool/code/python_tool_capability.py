import asyncio
from typing import Any

from pycraftcore.runtime import CodeFactory, Code
from pycraftcore.runtime.configuration import CodeStdout

from agentic.adapter.outbound.agent.tool.schema.tool_input import ToolInput
from agentic.adapter.outbound.agent.tool.schema.tool_result import ToolResult
from agentic.adapter.outbound.agent.tool.schema.python_tool_input import PythonToolInput


class PythonToolCapability:
    def __init__(
        self,
        code_factory: CodeFactory,
        name: str,
        description: str,
        args_schema: type[PythonToolInput],
        semaphore: asyncio.Semaphore,
    ) -> None:
        self._code_factory = code_factory
        self._name = name
        self._description = description
        self._args_schema = args_schema
        self._semaphore = semaphore

    @property
    def name(self) -> str:
        return self._name

    @property
    def args_schema(self) -> type[ToolInput]:
        return self._args_schema

    def schema(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "description": self._description,
            "parameters": self._args_schema.model_json_schema(),
        }

    async def execute(self, request: PythonToolInput) -> ToolResult:
        call_id: str = request.call_id or ""
        code: str = request.code

        if not code:
            return ToolResult(tool_name=self.name, id=call_id, output="", error="No code provided.")

        code_executor_proc: Code = self._code_factory(code=code, code_template=None)

        async with self._semaphore:
            code_result: CodeStdout = await code_executor_proc.execute()

        return ToolResult(
            tool_name=self.name, id=call_id, output=code_result.stdout, error=code_result.stderr
        )
