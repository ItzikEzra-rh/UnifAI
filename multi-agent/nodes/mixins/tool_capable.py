from typing import Iterable, Any


class ToolCapableMixin:
    """Adds post-processing tools."""

    def __init__(self, *, tools: Iterable[Any] = (), **_):
        self.tools = list(tools)

    def _apply_tools(self, text: str) -> str:
        res = text
        for tool in self.tools:
            res = tool.invoke(res)
        return res
