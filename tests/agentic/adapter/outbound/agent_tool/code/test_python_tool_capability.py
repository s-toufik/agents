import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock

from pycraftcore.runtime.configuration import CodeStdout

from agentic.adapter.outbound.agent_tool.code.python_tool_capability import PythonToolCapability
from agentic.adapter.outbound.agent_tool.schema.python_tool_input import PythonToolInput


def make_capability(code_factory, semaphore=None):
    return PythonToolCapability(
        code_factory=code_factory,
        name="python_executor",
        description="run python",
        args_schema=PythonToolInput,
        semaphore=semaphore or asyncio.Semaphore(8),
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


@pytest.mark.asyncio
async def test_execute_never_exceeds_semaphore_concurrency_limit():
    in_flight = 0
    max_observed = 0

    async def slow_execute():
        nonlocal in_flight, max_observed
        in_flight += 1
        max_observed = max(max_observed, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return CodeStdout(stdout="ok", stderr="")

    def make_executor(**_kwargs):
        executor = MagicMock()
        executor.execute = slow_execute
        return executor

    capability = make_capability(make_executor, semaphore=asyncio.Semaphore(2))

    requests = []
    for i in range(6):
        request = PythonToolInput(code="result = 1")
        request.call_id = f"call_{i}"
        requests.append(request)

    await asyncio.gather(*(capability.execute(request) for request in requests))

    assert max_observed <= 2
