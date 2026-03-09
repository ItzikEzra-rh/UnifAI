"""
Temporal graph executor.

Starts a GraphTraversalWorkflow on the shared Temporal task queue
and blocks until the result is ready.  This is the graph-execution
adapter — it knows nothing about session lifecycle.

Uses string-based workflow invocation to avoid importing from the
inbound adapter layer (hexagonal boundary compliance).
"""
import asyncio
import uuid
from typing import Any

from mas.engine.domain.base_executor import BaseGraphExecutor
from mas.engine.domain.models import GraphDefinition
from mas.graph.state.graph_state import GraphState
from mas.config.app_config import AppConfig
from temporal.client import get_temporal_client
from temporal.models import GraphExecutionParams

_WORKFLOW_NAME = "GraphTraversalWorkflow"


class TemporalGraphExecutor(BaseGraphExecutor):
    """
    Executes a graph via Temporal workflows.

    Holds only the GraphDefinition. Workers pick up activities and
    rebuild nodes from the mini-blueprints stored in each NodeDef.
    """

    def __init__(self, graph_def: GraphDefinition) -> None:
        self._graph_def = graph_def
        self._workflow_id: str | None = None

    @property
    def graph_definition(self) -> GraphDefinition:
        return self._graph_def

    def run(self, initial_state: Any) -> dict:
        state_dict = self._to_state_dict(initial_state)
        return asyncio.run(self._execute(state_dict))

    def stream(self, initial_state: Any, *args, **kwargs):
        final = self.run(initial_state)
        yield final

    def get_state(self) -> Any:
        if not self._workflow_id:
            return None
        return asyncio.run(self._query_state())

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _to_state_dict(self, initial_state: Any) -> dict:
        return (
            initial_state.serialize()
            if isinstance(initial_state, GraphState)
            else dict(initial_state)
        )

    async def _execute(self, state_dict: dict) -> dict:
        """Start GraphTraversalWorkflow and block until it completes."""
        cfg = AppConfig.get_instance()
        client = await get_temporal_client()

        workflow_id = f"graph-{uuid.uuid4().hex[:12]}"
        self._workflow_id = workflow_id

        params = GraphExecutionParams(
            state=state_dict,
            graph_definition=self._graph_def.model_dump(mode="json"),
        )
        return await client.execute_workflow(
            _WORKFLOW_NAME,
            params,
            id=workflow_id,
            task_queue=cfg.temporal_task_queue,
        )

    async def _query_state(self) -> dict:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(self._workflow_id)
        return await handle.query("get_state")
