import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic.adapter.outbound.agent.tool.sql.sql_tool_capability import SQLToolCapability
from agentic.adapter.outbound.agent.tool.schema.sql_tool_input import SQLToolInput


def make_capability(sql_handler, repository):
    return SQLToolCapability(
        repository=repository,
        sql_handler=sql_handler,
        name="users_tables",
        dialect="sqlite",
        description="run sql",
        args_schema=SQLToolInput,
    )


def make_request(query, dialect=None, call_id="call_1"):
    request = SQLToolInput(query=query, dialect=dialect or "")
    request.call_id = call_id
    return request


@pytest.mark.asyncio
async def test_blank_query_returns_error_without_calling_handler():
    sql_handler = MagicMock()
    repository = MagicMock()
    capability = make_capability(sql_handler, repository)

    result = await capability.execute(make_request("   "))

    sql_handler.assert_not_called()
    assert result.error == "No SQL query provided."


@pytest.mark.asyncio
async def test_handler_validation_error_is_caught_into_tool_result():
    sql_handler = MagicMock(side_effect=ValueError("bad sql"))
    repository = MagicMock()
    capability = make_capability(sql_handler, repository)

    result = await capability.execute(make_request("DROP TABLE users"))

    assert result.output == ""
    assert "SQL validation error" in result.error
    assert "bad sql" in result.error


@pytest.mark.asyncio
async def test_repository_execution_error_is_caught_into_tool_result():
    handler_instance = MagicMock()
    handler_instance.transpile.return_value = "SELECT * FROM users"
    sql_handler = MagicMock(return_value=handler_instance)
    repository = MagicMock()
    repository.execute = AsyncMock(side_effect=RuntimeError("db down"))
    capability = make_capability(sql_handler, repository)

    result = await capability.execute(make_request("SELECT * FROM users"))

    assert result.output == ""
    assert "SQL execution error" in result.error
    assert "db down" in result.error


@pytest.mark.asyncio
async def test_successful_execution_returns_stringified_rows():
    handler_instance = MagicMock()
    handler_instance.transpile.return_value = "SELECT * FROM users"
    sql_handler = MagicMock(return_value=handler_instance)
    repository = MagicMock()
    repository.execute = AsyncMock(return_value=[{"id": 1}])
    capability = make_capability(sql_handler, repository)

    result = await capability.execute(make_request("SELECT * FROM users"))

    assert result.error is None
    assert result.output == "[{'id': 1}]"


@pytest.mark.asyncio
async def test_request_dialect_overrides_default_dialect():
    handler_instance = MagicMock()
    handler_instance.transpile.return_value = "SELECT 1"
    sql_handler = MagicMock(return_value=handler_instance)
    repository = MagicMock()
    repository.execute = AsyncMock(return_value=[])
    capability = make_capability(sql_handler, repository)

    await capability.execute(make_request("SELECT 1", dialect="postgres"))

    sql_handler.assert_called_once_with("SELECT 1", dialect="postgres")


@pytest.mark.asyncio
async def test_falls_back_to_default_dialect_when_request_dialect_missing():
    handler_instance = MagicMock()
    handler_instance.transpile.return_value = "SELECT 1"
    sql_handler = MagicMock(return_value=handler_instance)
    repository = MagicMock()
    repository.execute = AsyncMock(return_value=[])
    capability = make_capability(sql_handler, repository)

    await capability.execute(make_request("SELECT 1"))

    sql_handler.assert_called_once_with("SELECT 1", dialect="sqlite")
