import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic.adapter.outbound.agent.tool.code.python_tool_capability import PythonToolCapability
from agentic.adapter.outbound.agent.tool.schema.python_tool_input import PythonToolInput
from agentic_core.infrastructure.runtime.code import CodeStdout


def make_capability(code_factory):
    return PythonToolCapability(
        code_factory=code_factory,
        name="python_executor",
        description="run python",
        args_schema=PythonToolInput,
        timeout=10,
        max_memory_mb=256,
    )


@pytest.mark.asyncio
async def test_empty_code_returns_error_without_calling_factory():
    code_factory = MagicMock()
    capability = make_capability(code_factory)
    request = PythonToolInput(code="")
    request.call_id = "call_1"

    result = await capability.execute(request)

    code_factory.assert_not_called()
    assert result.output == ""
    assert result.error == "No code provided."


@pytest.mark.asyncio
async def test_successful_execution_maps_stdout_and_stderr():
    executor = MagicMock()
    executor.execute = AsyncMock(return_value=CodeStdout(stdout="42", stderr=""))
    code_factory = MagicMock(return_value=executor)
    capability = make_capability(code_factory)
    request = PythonToolInput(code="result = 42")
    request.call_id = "call_1"

    result = await capability.execute(request)

    code_factory.assert_called_once()
    assert result.tool_name == "python_executor"
    assert result.id == "call_1"
    assert result.output == "42"
    assert result.error == ""


def test_schema_returns_name_description_and_json_schema():
    capability = make_capability(MagicMock())

    schema = capability.schema()

    assert schema["name"] == "python_executor"
    assert schema["description"] == "run python"
    assert "properties" in schema["parameters"]
