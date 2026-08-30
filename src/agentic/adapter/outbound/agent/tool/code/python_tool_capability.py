import asyncio
from typing import Any, Optional, cast

from pydantic import BaseModel

from agentic.adapter.outbound.agent.tool.schema.tool_result import ToolResult
from agentic.adapter.outbound.agent.tool.schema.python_tool_input import PythonToolInput
from agentic_core.infrastructure.runtime.code import CodeFactory, Code, CodeStdout
from agentic_core.infrastructure.logger.port.logger import Logger


class PythonToolCapability:
    def __init__(
        self,
        code_factory: CodeFactory,
        name: str,
        description: str,
        args_schema: type[BaseModel],
        timeout: int,
        max_memory_mb: int,
        semaphore: asyncio.Semaphore,
        logger: Optional[Logger] = None,
    ) -> None:
        self._code_factory = code_factory
        self._name = name
        self._description = description
        self._args_schema = args_schema
        self._timeout = timeout
        self._max_memory_mb = max_memory_mb
        self._semaphore = semaphore
        self._set_logging(logger)

    def _set_logging(self, logger: Logger | None) -> None:
        if logger is None:
            import logging

            self._logger: Logger = cast(Logger, logging.getLogger(__name__))
        else:
            self._logger: Logger = logger

    @property
    def name(self) -> str:
        return self._name

    @property
    def args_schema(self) -> type[BaseModel]:
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

        code_executor_proc: Code = self._code_factory(
            code=code,
            code_template=None,
            code_timeout=self._timeout,
            max_memory_mb=self._max_memory_mb,
        )

        async with self._semaphore:
            code_result: CodeStdout = await code_executor_proc.execute()

        return ToolResult(
            tool_name=self.name, id=call_id, output=code_result.stdout, error=code_result.stderr
        )
