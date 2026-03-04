"""
Temporal graph executor.

Starts a GraphTraversalWorkflow on the shared Temporal task queue.
Holds only the GraphDefinition (topology + node deployment info).

Uses lazy imports for Temporal SDK components to prevent circular
dependencies and avoid importing temporalio at module load time.
"""
import asyncio
import uuid
from typing import Any

from engine.domain.base_executor import BaseGraphExecutor
from engine.temporal.models import GraphDefinition
from graph.state.graph_state import GraphState
from config.app_config import AppConfig


class TemporalGraphExecutor(BaseGraphExecutor):
    """
    Starts a Temporal workflow to execute the graph.

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

    def start(self, initial_state: Any) -> str:
        """
        Non-blocking (fire-and-forget): submit the workflow and return
        the workflow_id immediately.
        """
        state_dict = self._to_state_dict(initial_state)
        return asyncio.run(self._start(state_dict))

    def stream(self, initial_state: Any, *args, **kwargs):
        final = self.run(initial_state)
        yield final

    def get_state(self) -> Any:
        if not self._workflow_id:
            return None
        return asyncio.run(self._query_state())

    def _to_state_dict(self, initial_state: Any) -> dict:
        return (
            initial_state.serialize()
            if isinstance(initial_state, GraphState)
            else dict(initial_state)
        )

    def _make_params(self, state_dict: dict) -> tuple:
        from temporal.models import GraphExecutionParams

        workflow_id = f"graph-{uuid.uuid4().hex[:12]}"
        self._workflow_id = workflow_id
        params = GraphExecutionParams(
            state=state_dict,
            graph_definition=self._graph_def.model_dump(mode="json"),
        )
        return workflow_id, params

    async def _execute(self, state_dict: dict) -> dict:
        from temporal.client import get_temporal_client
        from temporal.workflow import GraphTraversalWorkflow

        cfg = AppConfig.get_instance()
        client = await get_temporal_client()
        workflow_id, params = self._make_params(state_dict)
        return await client.execute_workflow(
            GraphTraversalWorkflow.run,
            params,
            id=workflow_id,
            task_queue=cfg.temporal_task_queue,
        )

    async def _start(self, state_dict: dict) -> str:
        from temporal.client import get_temporal_client
        from temporal.workflow import GraphTraversalWorkflow

        cfg = AppConfig.get_instance()
        client = await get_temporal_client()
        workflow_id, params = self._make_params(state_dict)
        await client.start_workflow(
            GraphTraversalWorkflow.run,
            params,
            id=workflow_id,
            task_queue=cfg.temporal_task_queue,
        )
        return workflow_id

    async def _query_state(self) -> dict:
        from temporal.client import get_temporal_client
        from temporal.workflow import GraphTraversalWorkflow

        client = await get_temporal_client()
        handle = client.get_workflow_handle(self._workflow_id)
        return await handle.query(GraphTraversalWorkflow.get_state)
