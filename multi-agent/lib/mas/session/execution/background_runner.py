"""
Canonical lifecycle runner for background session execution.

Defines the application-level ordering rule that ALL background engines
must follow:

    prepare  →  execute_graph  →  complete
                                   (or fail on error)

The ordering lives HERE, in the application layer — not inside any
infrastructure adapter.  Each adapter (Temporal, Celery, RQ, …)
implements BackgroundSessionOps to supply the engine-specific mechanics,
but the sequence is always driven by BackgroundSessionRunner.
"""
from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class BackgroundSessionOps(Protocol):
    """
    Engine-specific mechanics for background session execution.

    Each background engine implements these four async operations.
    The runner calls them in the canonical order.

    Temporal implements them as workflow activities / child workflows.
    Celery implements them as direct service calls inside a task.
    """

    async def prepare(self) -> dict:
        """Seed inputs, mark RUNNING, persist. Return seeded state dict."""
        ...

    async def execute_graph(self, seeded_state: dict) -> dict:
        """Run the graph and return the final state dict."""
        ...

    async def complete(self, final_state: dict) -> None:
        """Attach final state, mark COMPLETED, persist."""
        ...

    async def fail(self, error: Exception) -> None:
        """Mark FAILED, persist."""
        ...


class BackgroundSessionRunner:
    """
    Runs the full background session lifecycle.

    This is the single source of truth for the ordering rule.
    Infrastructure adapters supply BackgroundSessionOps; this class
    ensures they are called in the correct sequence.

    Mirrors ForegroundSessionRunner for the background path.
    """

    async def run(self, ops: BackgroundSessionOps) -> dict:
        """
        Execute the full background session lifecycle.

        Args:
            ops: Engine-specific operations (Temporal activities,
                 Celery service calls, etc.)

        Returns:
            The final graph state dict.
        """
        try:
            seeded_state = await ops.prepare()
            final_state = await ops.execute_graph(seeded_state)
            await ops.complete(final_state)
            return final_state
        except Exception as e:
            await ops.fail(e)
            raise
