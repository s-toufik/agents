from typing import Any

from pydantic import Field, create_model

from agentic.adapter.outbound.agent_tool.schema.tool_input import ToolInput

_JSON_SCHEMA_TYPES: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def build_tool_input(tool_name: str, input_schema: dict[str, Any]) -> type[ToolInput]:

    properties: dict[str, Any] = input_schema.get("properties", {})
    required: set[str] = set(input_schema.get("required", []))

    fields: dict[str, Any] = {}
    for property_name, property_schema in properties.items():
        python_type = _JSON_SCHEMA_TYPES.get(property_schema.get("type"), Any)
        description = property_schema.get("description")
        if property_name in required:
            fields[property_name] = (python_type, Field(..., description=description))
        else:
            fields[property_name] = (python_type | None, Field(None, description=description))

    return create_model(_model_name(tool_name), __base__=ToolInput, **fields)


def _model_name(tool_name: str) -> str:
    words = tool_name.replace("-", "_").split("_")
    return "Mcp" + "".join(word.capitalize() for word in words if word) + "Input"
