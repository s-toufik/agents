import pytest

from agentic.adapter.outbound.agent.tool.tool_registery import ToolRegistry


class FakeTool:
    def __init__(self, name, description="desc"):
        self._name = name
        self._description = description

    @property
    def name(self):
        return self._name

    def schema(self):
        return {"name": self._name, "description": self._description}


def test_get_returns_registered_tool_by_name():
    tool = FakeTool("tool_a")
    registry = ToolRegistry([tool])

    assert registry.get("tool_a") is tool


def test_get_raises_key_error_for_unknown_tool():
    registry = ToolRegistry([])

    with pytest.raises(KeyError):
        registry.get("missing")


def test_descriptions_returns_schema_for_every_tool():
    registry = ToolRegistry([FakeTool("a"), FakeTool("b")])

    descriptions = registry.descriptions()

    assert {d["name"] for d in descriptions} == {"a", "b"}


def test_duplicate_tool_names_last_one_wins():
    first = FakeTool("dup", description="first")
    second = FakeTool("dup", description="second")
    registry = ToolRegistry([first, second])

    assert registry.get("dup") is second
