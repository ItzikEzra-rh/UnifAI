from typing import List
from session.repository.repository import SessionRepository
from session.workflow_session_factory import WorkflowSessionFactory
from session.workflow_session import WorkflowSession
from schemas.blueprint.blueprint import BlueprintSpec


class UserSessionManager:
    """
    High‐level CRUD for user sessions.
    SRP: only creates, loads, and lists run_ids.
    """

    def __init__(
            self,
            repository: SessionRepository,
            session_factory: WorkflowSessionFactory
    ):
        self._repo = repository
        self._factory = session_factory

    def create_session(
            self,
            user_id: str,
            blueprint_spec: BlueprintSpec,
            metadata: dict = None
    ) -> WorkflowSession:
        """Instantiate a fresh session and persist it. Returns run_id."""
        session = self._factory.create(
            blueprint_spec=blueprint_spec,
            user_id=user_id,
            metadata=metadata
        )

        self._repo.save(session)
        return session

    def get_session(self, run_id: str) -> WorkflowSession:
        """Retrieve a previously created session."""
        return self._repo.load(run_id)

    def list_sessions(self, user_id: str) -> List[str]:
        """All run_ids belonging to this user."""
        return self._repo.list_runs(user_id)
