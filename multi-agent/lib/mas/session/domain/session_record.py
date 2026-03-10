"""
Lightweight, persistable representation of a session.

Contains only the data needed for storage and retrieval —
no runtime artifacts (no graph plan, no executable graph, no node instances).

Used by:
  - create_session: build a record cheaply without compiling a graph
  - SessionRepository: typed save/fetch interface
  - SessionLifecycle: mutate status/state and persist
  - BackgroundLifecycleHandler: avoid expensive full-session hydration
"""
from dataclasses import dataclass

from mas.core.run_context import RunContext
from mas.graph.state.graph_state import GraphState
from mas.session.domain.models import SessionMeta
from mas.session.domain.status import SessionStatus


@dataclass
class SessionRecord:
    run_id: str
    user_id: str
    blueprint_id: str
    run_context: RunContext
    metadata: SessionMeta
    graph_state: GraphState
    status: SessionStatus
