from agentic.adapter.outbound.agent_tool.mcp.mcp_tool_input_factory import build_tool_input
from agentic.adapter.outbound.agent_tool.schema.tool_input import ToolInput


def test_required_and_optional_fields_are_reflected_in_the_schema():
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "the search query"},
            "limit": {"type": "integer", "description": "max results"},
        },
        "required": ["query"],
    }

    model = build_tool_input("search-docs", input_schema)
    instance = model(query="hello")

    assert issubclass(model, ToolInput)
    assert instance.query == "hello"
    assert instance.limit is None


def test_missing_required_field_raises_validation_error():
    input_schema = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    model = build_tool_input("search-docs", input_schema)

    try:
        model()
    except Exception as exception:
        assert "query" in str(exception)
    else:
        raise AssertionError("expected a validation error for the missing required field")


def test_model_name_is_derived_from_the_tool_name():
    model = build_tool_input("search_docs", {"properties": {}, "required": []})

    assert model.__name__ == "McpSearchDocsInput"


def test_hyphenated_tool_name_is_normalized_like_an_underscore():
    model = build_tool_input("search-docs", {"properties": {}, "required": []})

    assert model.__name__ == "McpSearchDocsInput"


def test_unknown_json_schema_type_falls_back_to_any():
    input_schema = {
        "properties": {"payload": {"type": "unknown-type"}},
        "required": ["payload"],
    }

    model = build_tool_input("weird_tool", input_schema)
    instance = model(payload={"anything": True})

    assert instance.payload == {"anything": True}


def test_tool_input_still_carries_call_id():
    model = build_tool_input("noop", {"properties": {}, "required": []})
    instance = model()
    instance.call_id = "call_1"

    assert instance.call_id == "call_1"
