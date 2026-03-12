from typing import Any

from mas.engine.domain.base_executor import BaseGraphExecutor
from mas.engine.domain.types import DEFAULT_RECURSION_LIMIT


class LangGraphExecutor(BaseGraphExecutor):
    """
    Wraps a LangGraph compiled graph (which has .invoke),
    exposing it as a BaseGraphExecutor with .run().
    """

    def __init__(
        self,
        compiled_graph: Any,
        recursion_limit: int = DEFAULT_RECURSION_LIMIT,
    ) -> None:
        self._compiled = compiled_graph
        self._recursion_limit = recursion_limit

    def run(self, initial_state: Any, *, session_id: str = "") -> Any:
        return self._compiled.invoke(
            initial_state,
            config={"recursion_limit": self._recursion_limit},
        )

    def get_state(self) -> Any:
        return self._compiled.get_state(None)
