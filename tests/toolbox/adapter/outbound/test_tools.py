import asyncio

import pytest

from toolbox.adapter.outbound.code.python_tool import PythonTool
from toolbox.adapter.outbound.sql.sql_tool import SqlTool
from toolbox.domain.model.tool_invocation import ToolInvocation
from toolbox.domain.model.tool_specification import ToolSpecification

SPEC = ToolSpecification(name="tool", description="A tool.")


class StubCode:
    def __init__(self, stdout: str, stderr: str) -> None:
        self._stdout = stdout
        self._stderr = stderr

    async def execute(self):
        from pycraftcore.runtime.configuration import CodeStdout

        return CodeStdout(stdout=self._stdout, stderr=self._stderr)


def code_factory(stdout: str = "", stderr: str = ""):
    def factory(code: str, code_template=None):
        return StubCode(stdout, stderr)

    return factory


class StubRepository:
    def __init__(self, rows=None, error: Exception | None = None) -> None:
        self._rows = rows or []
        self._error = error
        self.executed: list[str] = []

    async def execute(self, sql: str, parameters=()):
        if self._error:
            raise self._error
        self.executed.append(sql)
        return self._rows


class StubQueryHandler:
    def __init__(self, expression: str, error: Exception | None = None) -> None:
        self._expression = expression
        self._error = error

    def transpile(self, expressions=None) -> str:
        if self._error:
            raise self._error
        return self._expression


def query_factory(error: Exception | None = None):
    def factory(expression: str, dialect: str):
        return StubQueryHandler(expression, error)

    return factory


@pytest.fixture
def semaphore() -> asyncio.Semaphore:
    return asyncio.Semaphore(1)


async def test_python_tool_returns_stdout(semaphore) -> None:
    tool = PythonTool(code_factory(stdout="42"), SPEC, semaphore)

    outcome = await tool.invoke(ToolInvocation(id="1", name="tool", arguments={"code": "x=1"}))

    assert outcome.output == "42"
    assert not outcome.failed


async def test_python_tool_keeps_stdout_alongside_stderr(semaphore) -> None:
    tool = PythonTool(code_factory(stdout="partial", stderr="boom"), SPEC, semaphore)

    outcome = await tool.invoke(ToolInvocation(id="1", name="tool", arguments={"code": "x=1"}))

    assert outcome.failed
    assert "partial" in outcome.content
    assert "boom" in outcome.content


async def test_python_tool_rejects_empty_code(semaphore) -> None:
    tool = PythonTool(code_factory(), SPEC, semaphore)

    outcome = await tool.invoke(ToolInvocation(id="1", name="tool", arguments={"code": "   "}))

    assert outcome.failed


async def test_sql_tool_executes_the_transpiled_statement() -> None:
    repository = StubRepository(rows=[{"n": 1}])
    tool = SqlTool(repository, query_factory(), SPEC, "sqlite")

    outcome = await tool.invoke(
        ToolInvocation(id="1", name="tool", arguments={"query": "select 1"})
    )

    assert repository.executed == ["select 1"]
    assert outcome.output == "[{'n': 1}]"


async def test_sql_tool_never_reaches_the_database_on_invalid_sql() -> None:
    repository = StubRepository()
    tool = SqlTool(repository, query_factory(ValueError("forbidden")), SPEC, "sqlite")

    outcome = await tool.invoke(
        ToolInvocation(id="1", name="tool", arguments={"query": "drop table t"})
    )

    assert repository.executed == []
    assert outcome.failed
    assert "validation" in (outcome.error or "")


async def test_sql_tool_rejects_an_empty_query_without_touching_anything() -> None:
    repository = StubRepository()
    tool = SqlTool(repository, query_factory(), SPEC, "sqlite")

    outcome = await tool.invoke(ToolInvocation(id="1", name="tool", arguments={"query": "   "}))

    assert repository.executed == []
    assert outcome.failed
    assert "No SQL query" in (outcome.error or "")


async def test_sql_tool_surfaces_a_repository_execution_error() -> None:
    repository = StubRepository(error=RuntimeError("db is gone"))
    tool = SqlTool(repository, query_factory(), SPEC, "sqlite")

    outcome = await tool.invoke(ToolInvocation(id="1", name="tool", arguments={"query": "select 1"}))

    assert outcome.failed
    assert "db is gone" in (outcome.error or "")


def test_sql_tool_exposes_its_specification() -> None:
    tool = SqlTool(StubRepository(), query_factory(), SPEC, "sqlite")

    assert tool.specification is SPEC


def test_python_tool_exposes_its_specification(semaphore) -> None:
    tool = PythonTool(code_factory(), SPEC, semaphore)

    assert tool.specification is SPEC
