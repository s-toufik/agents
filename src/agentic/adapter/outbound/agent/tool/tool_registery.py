from typing import Any

from agentic.adapter.outbound.agent.tool.tool_capabilities import ToolCapability


class ToolRegistry:
    def __init__(self, tools: list[ToolCapability]) -> None:
        self._tools: dict[str, ToolCapability] = {tool.name: tool for tool in tools}

    def get(self, name: str) -> ToolCapability:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"No tool registered: '{name}'.")
        return tool

    def descriptions(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]
