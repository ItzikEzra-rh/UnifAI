"""
Session lifecycle state-machine transitions.

Operates on SessionRecord (the persistable layer) so that both foreground
runners and background workers can share the same logic without requiring
a full WorkflowSession.
"""
from typing import Any, Dict

from mas.graph.state.graph_state import GraphState
from mas.session.repository.repository import SessionRepository
from mas.session.domain.session_record import SessionRecord
from mas.session.domain.status import SessionStatus
from mas.session.management.utils import derive_title
from mas.core.context import set_current_context


class SessionLifecycle:
    """
    Owns the prepare / complete / fail transitions of a SessionRecord.

    Stateless — all state lives in the SessionRecord and the repository.
    """

    def __init__(self, repository: SessionRepository) -> None:
        self._repo = repository

    def prepare(
        self,
        record: SessionRecord,
        inputs: Dict[str, Any],
        scope: str,
        logged_in_user: str,
    ) -> None:
        """
        Pre-execution: seed inputs, bind context, mark RUNNING, persist.
        """
        if record.metadata.title is None:
            if title := derive_title(inputs):
                record.metadata.title = title

        ctx = record.run_context.change_scope(scope)
        ctx = ctx.set_logged_in_user(logged_in_user)
        set_current_context(ctx)
        record.run_context = ctx

        record.graph_state.update(inputs)
        record.status = SessionStatus.RUNNING
        self._repo.save(record)

    def complete(
        self,
        record: SessionRecord,
        final_state: Any,
    ) -> None:
        """
        Post-execution: attach final state, mark COMPLETED, persist.
        """
        if isinstance(final_state, dict):
            record.graph_state = GraphState(**final_state)
        else:
            record.graph_state = final_state

        record.run_context = record.run_context.mark_finished()
        set_current_context(record.run_context)
        record.status = SessionStatus.COMPLETED
        self._repo.save(record)

    def fail(
        self,
        record: SessionRecord,
        error: Exception,
    ) -> None:
        """
        On error: mark FAILED, persist.
        """
        record.run_context = record.run_context.mark_finished()
        record.status = SessionStatus.FAILED
        self._repo.save(record)
