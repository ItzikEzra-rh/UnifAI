"""
Temporal-native graph executor.

Starts an embedded Temporal worker with the graph's node callables
registered as activity methods, then runs a GraphTraversalWorkflow
to traverse the graph.  Mirrors LangGraphExecutor: where LG calls
compiled.invoke(), we start a workflow that calls activities.
"""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from config.app_config import AppConfig
from engine.executor.interfaces import GraphExecutor
from engine.models import GraphDefinition
from graph.state.graph_state import GraphState
from temporal.client import get_temporal_client
from temporal.graph_models import GraphExecutionParams
from temporal.graph_node_activities import GraphNodeActivities
from temporal.graph_workflow import GraphTraversalWorkflow


class TemporalGraphExecutor(GraphExecutor):
    """
    Executes a graph through Temporal.

    Holds:
      • graph_def  — topology (serializable, sent to workflow)
      • activities — node callables wrapped as activity methods

    On run():
      1. Starts an embedded worker with the activities registered
      2. Starts GraphTraversalWorkflow on a unique task queue
      3. Waits for the workflow to complete
      4. Shuts down the worker
      5. Returns the final state

    The unique task queue ensures this worker handles only THIS
    execution's activities — no interference between concurrent runs.
    """

    def __init__(
            self,
            graph_def: GraphDefinition,
            activities: GraphNodeActivities,
    ) -> None:
        self._graph_def = graph_def
        self._activities = activities
        self._workflow_id: str | None = None

    @property
    def graph_definition(self) -> GraphDefinition:
        return self._graph_def

    def run(self, initial_state: Any) -> dict:
        state_dict = (
            initial_state.serialize()
            if isinstance(initial_state, GraphState)
            else dict(initial_state)
        )
        return asyncio.run(self._execute(state_dict))

    def stream(self, initial_state: Any, *args, **kwargs):
        final = self.run(initial_state)
        yield final

    def get_state(self) -> Any:
        if not self._workflow_id:
            return None
        return asyncio.run(self._query_state())

    # ------------------------------------------------------------------ #
    #  Private async implementation
    # ------------------------------------------------------------------ #

    async def _execute(self, state_dict: dict) -> dict:
        client = await get_temporal_client()

        # Unique task queue → isolates this execution's activities
        task_queue = f"graph-exec-{uuid.uuid4().hex[:12]}"
        workflow_id = f"graph-{uuid.uuid4().hex[:12]}"
        self._workflow_id = workflow_id

        params = GraphExecutionParams(
            state=state_dict,
            graph_definition=self._graph_def.model_dump(),
        )

        activity_executor = ThreadPoolExecutor(max_workers=5)
        worker = Worker(
            client,
            task_queue=task_queue,
            workflows=[GraphTraversalWorkflow],
            activities=[
                self._activities.execute_node,
                self._activities.evaluate_condition,
            ],
            activity_executor=activity_executor,
            # Sandbox is unnecessary — this worker is embedded (same process,
            # ephemeral, one execution). Disabling it avoids restrictions on
            # modules that use datetime.utcnow or other non-deterministic defaults.
            workflow_runner=UnsandboxedWorkflowRunner(),
        )

        # Run worker in background, execute workflow, then shut down
        worker_task = asyncio.create_task(worker.run())
        try:
            result = await client.execute_workflow(
                GraphTraversalWorkflow.run,
                params,
                id=workflow_id,
                task_queue=task_queue,
            )
            return result
        finally:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
            activity_executor.shutdown(wait=False)

    async def _query_state(self) -> dict:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(self._workflow_id)
        return await handle.query(GraphTraversalWorkflow.get_state)
