"""
Temporal adapter for background session submission.

Implements the session-level BackgroundSessionSubmitter port.
Starts a durable SessionWorkflow that owns the full session lifecycle
(prepare → execute → complete/fail) inside the Temporal cluster.

Uses string-based workflow invocation to avoid importing from the
inbound adapter layer (hexagonal boundary compliance).
"""
import asyncio
import uuid

from mas.graph.state.graph_state import GraphState
from mas.session.execution.ports import BackgroundSessionSubmitter, SubmitSessionRequest
from mas.session.domain.workflow_session import WorkflowSession
from mas.config.app_config import AppConfig
from temporal.client import get_temporal_client
from temporal.models import SessionWorkflowParams, GraphExecutionParams
from outbound.temporal.executor import TemporalGraphExecutor

_WORKFLOW_NAME = "SessionWorkflow"


class TemporalSessionSubmitter(BackgroundSessionSubmitter):
    """
    Submits sessions to Temporal for durable background execution.

    The SessionWorkflow handles the entire lifecycle:
      prepare_session activity  → seed inputs, mark RUNNING
      GraphTraversalWorkflow    → graph execution (child workflow)
      complete_session activity → mark COMPLETED
      On error: fail_session    → mark FAILED

    Requires the session's executable_graph to be a TemporalGraphExecutor
    (both live in the same outbound/temporal adapter boundary).
    """

    def submit(self, session: WorkflowSession, request: SubmitSessionRequest) -> str:
        return asyncio.run(self._start_session_workflow(session, request))

    async def _start_session_workflow(
        self,
        session: WorkflowSession,
        request: SubmitSessionRequest,
    ) -> str:
        executor = session.executable_graph
        if not isinstance(executor, TemporalGraphExecutor):
            raise TypeError(
                f"TemporalSessionSubmitter requires a TemporalGraphExecutor, "
                f"got {type(executor).__name__}. "
                f"Ensure the session was built with engine_name='temporal'."
            )

        cfg = AppConfig.get_instance()
        client = await get_temporal_client()

        graph_def = executor.graph_definition
        state_dict = (
            session.graph_state.serialize()
            if isinstance(session.graph_state, GraphState)
            else dict(session.graph_state)
        )

        workflow_id = f"session-{uuid.uuid4().hex[:12]}"

        graph_params = GraphExecutionParams(
            state=state_dict,
            graph_definition=graph_def.model_dump(mode="json"),
            session_id=session.get_run_id(),
        )
        params = SessionWorkflowParams(
            run_id=session.get_run_id(),
            inputs=request.inputs,
            scope=request.scope,
            logged_in_user=request.logged_in_user,
            graph_execution_params=graph_params.model_dump(mode="json"),
        )
        await client.start_workflow(
            _WORKFLOW_NAME,
            params,
            id=workflow_id,
            task_queue=cfg.temporal_task_queue,
        )
        return workflow_id
