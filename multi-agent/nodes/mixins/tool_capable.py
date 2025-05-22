from typing import Iterable, Any


class ToolCapableMixin:
    """Adds post-processing tools."""

    def __init__(self, *, tools: Iterable[Any] = (), **kwargs: Any):
        super().__init__(**kwargs)  # MRO
        self.tools = list(tools)

    def _apply_tools(self, text: str) -> str:
        res = text
        for tool in self.tools:
            res = tool.invoke(res)
        return res
