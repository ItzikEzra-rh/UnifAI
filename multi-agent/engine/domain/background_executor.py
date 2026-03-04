from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ExecutionContext:
    """
    Immutable context passed to background executors for fire-and-forget
    submission.  Carries everything the durable workflow needs to run
    the full session lifecycle (prepare → execute → complete/fail)
    without the API process being involved.
    """
    run_id: str
    inputs: Dict[str, Any]
    scope: str
    logged_in_user: str


class BackgroundExecutor(ABC):
    """
    Interface for executors that support fire-and-forget submission.

    Concrete examples: TemporalGraphExecutor (starts a durable workflow
    and returns a handle immediately).  LangGraphExecutor does NOT
    implement this — it only supports blocking execution.
    """

    @abstractmethod
    def start(self, initial_state: Any, context: ExecutionContext) -> str:
        """
        Submit the graph for background execution.

        The durable workflow is responsible for the full session lifecycle
        (prepare, execute, complete/fail).

        Args:
            initial_state: The initial graph state (before input seeding).
            context: Execution context carrying run_id, inputs, scope, etc.

        Returns:
            A workflow handle / ID the caller can use for polling.
        """
        ...
