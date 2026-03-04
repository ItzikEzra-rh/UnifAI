"""
Temporal session workflow — parent workflow.

Orchestrates session lifecycle around graph traversal:
  1. Run GraphTraversalWorkflow as a child workflow
  2. On success → complete_session activity (lifecycle.complete)
  3. On failure → fail_session activity (lifecycle.fail)

The GraphTraversalWorkflow stays pure (graph logic only).
Session lifecycle is handled at this layer.
"""
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.models import (
    SessionWorkflowParams,
    GraphExecutionParams,
    CompleteSessionParams,
    FailSessionParams,
)

_LIFECYCLE_TIMEOUT = timedelta(seconds=30)
_LIFECYCLE_RETRY = RetryPolicy(maximum_attempts=3)

_GRAPH_WORKFLOW_TIMEOUT = timedelta(hours=1)


@workflow.defn
class SessionWorkflow:
    """
    Parent workflow for fire-and-forget session execution.

    Composes GraphTraversalWorkflow (child) with lifecycle
    activities so the session status is properly updated
    even when the API process has already returned 202.
    """

    @workflow.run
    async def run(self, params: SessionWorkflowParams) -> dict:
        from temporal.workflow import GraphTraversalWorkflow

        graph_params = GraphExecutionParams.model_validate(
            params.graph_execution_params,
        )

        try:
            final_state = await workflow.execute_child_workflow(
                GraphTraversalWorkflow.run,
                graph_params,
                id=f"{workflow.info().workflow_id}-graph",
                execution_timeout=_GRAPH_WORKFLOW_TIMEOUT,
            )

            await workflow.execute_activity(
                "complete_session",
                CompleteSessionParams(
                    run_id=params.run_id,
                    final_state=final_state,
                ),
                start_to_close_timeout=_LIFECYCLE_TIMEOUT,
                retry_policy=_LIFECYCLE_RETRY,
            )

            return final_state

        except Exception as e:
            await workflow.execute_activity(
                "fail_session",
                FailSessionParams(
                    run_id=params.run_id,
                    error_message=str(e),
                ),
                start_to_close_timeout=_LIFECYCLE_TIMEOUT,
                retry_policy=_LIFECYCLE_RETRY,
            )
            raise
