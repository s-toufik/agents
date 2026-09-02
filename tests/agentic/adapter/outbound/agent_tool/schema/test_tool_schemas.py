from agentic.adapter.outbound.agent_tool.schema.python_tool_input import PythonToolInput
from agentic.adapter.outbound.agent_tool.schema.sql_tool_input import SQLToolInput
from agentic.adapter.outbound.agent_tool.schema.tool_result import ToolResult


def test_python_tool_input_call_id_getter_setter_round_trip():
    tool_input = PythonToolInput(code="print(1)")
    tool_input.call_id = "call_1"

    assert tool_input.call_id == "call_1"
    assert tool_input.code == "print(1)"


def test_sql_tool_input_call_id_getter_setter_round_trip():
    tool_input = SQLToolInput(query="SELECT 1", dialect="sqlite")
    tool_input.call_id = "call_2"

    assert tool_input.call_id == "call_2"
    assert tool_input.query == "SELECT 1"
    assert tool_input.dialect == "sqlite"


def test_tool_result_content_returns_output_when_no_error():
    result = ToolResult(tool_name="t", id="1", output="42")

    assert result.content == "42"


def test_tool_result_content_returns_formatted_error_when_present():
    result = ToolResult(tool_name="t", id="1", output="", error="boom")

    assert result.content == "Error: boom"
