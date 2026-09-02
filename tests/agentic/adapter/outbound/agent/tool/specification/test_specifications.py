from pycraftcore.query_language.constants import FORBIDDEN_SQL_EXPRESSIONS
from pycraftcore.runtime.adapter.python.adapter import PYTHON_ALLOWLIST

from agentic.adapter.outbound.agent.tool.specification import python_sandbox, user_sqlite_repository


def test_python_sandbox_description_mentions_every_allowed_module():
    for module in PYTHON_ALLOWLIST:
        assert module in python_sandbox.description


def test_python_sandbox_args_schema_is_python_tool_input():
    from agentic.adapter.outbound.agent.tool.schema.python_tool_input import PythonToolInput

    assert python_sandbox.args_schema is PythonToolInput


def test_user_sqlite_repository_description_mentions_every_forbidden_statement():
    for statement in FORBIDDEN_SQL_EXPRESSIONS:
        assert statement.__name__ in user_sqlite_repository.description


def test_user_sqlite_repository_args_schema_is_sql_tool_input():
    from agentic.adapter.outbound.agent.tool.schema.sql_tool_input import SQLToolInput

    assert user_sqlite_repository.args_schema is SQLToolInput
