"""
Temporal graph executor.

Starts workflows on the shared Temporal task queue.
- run()   → blocking: starts GraphTraversalWorkflow and waits for result.
- start() → fire-and-forget: starts SessionWorkflow (which wraps
            GraphTraversalWorkflow + lifecycle activities) and returns
            the workflow_id immediately.

Uses lazy imports for Temporal SDK components to prevent circular
dependencies and avoid importing temporalio at module load time.
"""
import asyncio
import uuid
from typing import Any

from engine.domain.base_executor import BaseGraphExecutor
from engine.domain.background_executor import BackgroundExecutor, ExecutionContext
from engine.domain.models import GraphDefinition
from graph.state.graph_state import GraphState
from config.app_config import AppConfig


class TemporalGraphExecutor(BaseGraphExecutor, BackgroundExecutor):
    """
    Starts Temporal workflows to execute the graph.

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

    def start(self, initial_state: Any, context: ExecutionContext) -> str:
        """
        Fire-and-forget: submit a SessionWorkflow and return the
        workflow_id immediately.  The SessionWorkflow handles the
        full session lifecycle (prepare → execute → complete/fail).
        """
        state_dict = self._to_state_dict(initial_state)
        return asyncio.run(self._start_session_workflow(state_dict, context))

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
        """Blocking: start GraphTraversalWorkflow and wait for the result."""
        from infrastructure.temporal.client import get_temporal_client
        from infrastructure.temporal.workflow import GraphTraversalWorkflow
        from infrastructure.temporal.models import GraphExecutionParams

        cfg = AppConfig.get_instance()
        client = await get_temporal_client()

        workflow_id = f"graph-{uuid.uuid4().hex[:12]}"
        self._workflow_id = workflow_id

        params = GraphExecutionParams(
            state=state_dict,
            graph_definition=self._graph_def.model_dump(mode="json"),
        )
        return await client.execute_workflow(
            GraphTraversalWorkflow.run,
            params,
            id=workflow_id,
            task_queue=cfg.temporal_task_queue,
        )

    async def _start_session_workflow(
        self, state_dict: dict, context: ExecutionContext,
    ) -> str:
        """Fire-and-forget: start SessionWorkflow (parent) which handles
        the full session lifecycle (prepare → execute → complete/fail)."""
        from infrastructure.temporal.client import get_temporal_client
        from infrastructure.temporal.session_workflow import SessionWorkflow
        from infrastructure.temporal.models import SessionWorkflowParams, GraphExecutionParams

        cfg = AppConfig.get_instance()
        client = await get_temporal_client()

        workflow_id = f"session-{uuid.uuid4().hex[:12]}"
        self._workflow_id = workflow_id

        graph_params = GraphExecutionParams(
            state=state_dict,
            graph_definition=self._graph_def.model_dump(mode="json"),
        )
        params = SessionWorkflowParams(
            run_id=context.run_id,
            inputs=context.inputs,
            scope=context.scope,
            logged_in_user=context.logged_in_user,
            graph_execution_params=graph_params.model_dump(mode="json"),
        )
        await client.start_workflow(
            SessionWorkflow.run,
            params,
            id=workflow_id,
            task_queue=cfg.temporal_task_queue,
        )
        return workflow_id

    async def _query_state(self) -> dict:
        from infrastructure.temporal.client import get_temporal_client
        from infrastructure.temporal.workflow import GraphTraversalWorkflow

        client = await get_temporal_client()
        handle = client.get_workflow_handle(self._workflow_id)
        return await handle.query(GraphTraversalWorkflow.get_state)
