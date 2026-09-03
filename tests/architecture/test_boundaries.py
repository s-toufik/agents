"""The rule that makes two processes worth it.

`agent` and `toolbox` are separate hexagons: they share pycraftcore and the MCP
wire protocol, and nothing else. If one ever imports the other, the split has
silently collapsed back into a monolith and the toolbox is no longer
independently deployable.
"""

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "src"


def _imported_roots(package: str) -> set[str]:
    roots: set[str] = set()
    for path in (SOURCE / package).rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots.add(node.module.split(".", 1)[0])
    return roots


def test_agent_does_not_import_toolbox() -> None:
    assert "toolbox" not in _imported_roots("agent")


def test_toolbox_does_not_import_agent() -> None:
    assert "agent" not in _imported_roots("toolbox")


def test_toolbox_does_not_import_langchain_or_langgraph() -> None:
    roots = _imported_roots("toolbox")
    assert not roots & {"langchain", "langchain_core", "langchain_openai", "langgraph"}


def test_neither_hexagon_imports_bootstrap() -> None:
    assert "bootstrap" not in _imported_roots("agent")
    assert "bootstrap" not in _imported_roots("toolbox")


def test_domain_layers_stay_free_of_frameworks() -> None:
    forbidden = {"fastapi", "starlette", "mcp", "langchain", "langgraph", "pydantic"}
    for package in ("agent", "toolbox"):
        for path in (SOURCE / package / "domain").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.Import):
                    module = node.names[0].name.split(".", 1)[0]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module = node.module.split(".", 1)[0]
                assert module not in forbidden, f"{path} imports {module}"
