"""
Temporal activity wrapper for session lifecycle transitions.

Pure one-liner delegates to the domain-level BackgroundSessionExecutor.
"""
from temporalio import activity

from mas.session.execution.background_executor import BackgroundSessionExecutor
from temporal.models import (
    PrepareSessionParams,
    CompleteSessionParams,
    FailSessionParams,
)


class SessionLifecycleActivities:
    """Pure one-liner delegates to BackgroundSessionExecutor."""

    def __init__(self, executor: BackgroundSessionExecutor) -> None:
        self._executor = executor

    @activity.defn(name="prepare_session")
    def prepare_session(self, params: PrepareSessionParams) -> dict:
        return self._executor.prepare(
            params.run_id, params.inputs, params.scope, params.logged_in_user,
        )

    @activity.defn(name="complete_session")
    def complete_session(self, params: CompleteSessionParams) -> None:
        self._executor.complete(params.run_id, params.final_state)

    @activity.defn(name="fail_session")
    def fail_session(self, params: FailSessionParams) -> None:
        self._executor.fail(params.run_id, params.error_message)
