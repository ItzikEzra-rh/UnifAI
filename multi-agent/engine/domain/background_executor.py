from abc import ABC, abstractmethod
from typing import Any


class BackgroundExecutor(ABC):
    """
    Interface for executors that support fire-and-forget submission.

    Concrete examples: TemporalGraphExecutor (starts a durable workflow
    and returns a handle immediately).  LangGraphExecutor does NOT
    implement this — it only supports blocking execution.
    """

    @abstractmethod
    def start(self, initial_state: Any, run_id: str) -> str:
        """
        Submit the graph for background execution.

        Args:
            initial_state: The initial graph state.
            run_id: Session run ID so the workflow can complete the
                    session lifecycle when done.

        Returns:
            A workflow handle / ID the caller can use for polling.
        """
        ...
