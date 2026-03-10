"""
Temporal activity wrapper for session lifecycle transitions.

Pure one-liner delegates to the domain-level BackgroundLifecycleHandler.
"""
from temporalio import activity

from mas.session.execution.lifecycle_handler import BackgroundLifecycleHandler
from temporal.models import (
    PrepareSessionParams,
    CompleteSessionParams,
    FailSessionParams,
)


class SessionLifecycleActivities:
    """Pure one-liner delegates to BackgroundLifecycleHandler."""

    def __init__(self, handler: BackgroundLifecycleHandler) -> None:
        self._handler = handler

    @activity.defn(name="prepare_session")
    def prepare_session(self, params: PrepareSessionParams) -> dict:
        return self._handler.prepare(
            params.run_id, params.inputs, params.scope, params.logged_in_user,
        )

    @activity.defn(name="complete_session")
    def complete_session(self, params: CompleteSessionParams) -> None:
        self._handler.complete(params.run_id, params.final_state)

    @activity.defn(name="fail_session")
    def fail_session(self, params: FailSessionParams) -> None:
        self._handler.fail(params.run_id, params.error_message)
