from agentic.agent.tools.tool_capabilities import ToolCapability


class ToolRegistry:

    def __init__(self, tools: list[ToolCapability]) -> None:
        self._tools: dict[str, ToolCapability] = {t.name: t for t in tools}

    def get(self, name: str) -> ToolCapability:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"No tool registered: '{name}'.")
        return tool

    def descriptions(self) -> str:
        return "\n".join(
            f"  • {t.name} — {t.description}" for t in self._tools.values()
        )