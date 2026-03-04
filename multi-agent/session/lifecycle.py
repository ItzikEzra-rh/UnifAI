"""
Session lifecycle state-machine transitions.

Portable across execution contexts: can be called from the API process
(synchronous run/stream) or from a Temporal activity (async completion).
"""
from typing import Any, Dict

from graph.state.graph_state import GraphState
from session.repository.repository import SessionRepository
from session.workflow_session import WorkflowSession
from session.status import SessionStatus
from session.utils import derive_title
from core.context import set_current_context


class SessionLifecycle:
    """
    Owns the prepare / complete / fail transitions of a WorkflowSession.

    Stateless — all state lives in the WorkflowSession and the repository.
    """

    def __init__(self, repository: SessionRepository) -> None:
        self._repo = repository

    def prepare(
        self,
        session: WorkflowSession,
        inputs: Dict[str, Any],
        scope: str,
        logged_in_user: str,
    ) -> None:
        """
        Pre-execution: seed inputs, bind context, mark RUNNING, persist.
        """
        if session.metadata.title is None:
            if title := derive_title(inputs):
                session.metadata.title = title

        ctx = session.run_context.change_scope(scope)
        ctx = ctx.set_logged_in_user(logged_in_user)
        set_current_context(ctx)
        session.run_context = ctx

        session.graph_state.update(inputs)
        session.update_status(SessionStatus.RUNNING)
        self._repo.save(session)

    def complete(
        self,
        session: WorkflowSession,
        final_state: Any,
    ) -> None:
        """
        Post-execution: attach final state, mark COMPLETED, persist.
        """
        if isinstance(final_state, dict):
            session.graph_state = GraphState(**final_state)
        else:
            session.graph_state = final_state

        session.run_context = session.run_context.mark_finished()
        set_current_context(session.run_context)
        session.update_status(SessionStatus.COMPLETED)
        self._repo.save(session)

    def fail(
        self,
        session: WorkflowSession,
        error: Exception,
    ) -> None:
        """
        On error: mark FAILED, persist.
        """
        session.run_context = session.run_context.mark_finished()
        session.update_status(SessionStatus.FAILED)
        self._repo.save(session)
