import pymongo
from pymongo.collection import Collection
from typing import List

from session.repository.repository import SessionRepository
from session.workflow_session import WorkflowSession
from core.run_context import RunContext
from graph.graph_state import GraphState
from session.workflow_session_factory import WorkflowSessionFactory
from schemas.blueprint.blueprint import BlueprintSpec


class MongoSessionRepository(SessionRepository):
    """
    A “light” MongoDB‐backed SessionRepository.

    Persists only:
      - run_context (so we keep the original run_id & timestamps)
      - blueprint_path (to recreate via factory)
      - metadata (user tags, etc.)
      - graph_state (the key→value bag)

    On load, we simply re-run the factory and then inject the saved state & context.
    """

    def __init__(
            self,
            session_factory: WorkflowSessionFactory,
            db_name: str = "UnifAI",
            mongo_uri: str = "mongodb://localhost:27017/",
            collection_name: str = "workflow_sessions",
    ):
        # connect
        client = pymongo.MongoClient(mongo_uri)
        db = client[db_name]
        self._col: Collection = db[collection_name]
        self._col.create_index(
            [("user_id", pymongo.ASCENDING), ("run_id", pymongo.ASCENDING)],
            unique=True
        )

        # DI: factory that knows how to build a fresh session from blueprint
        self._factory = session_factory

    def save(self, session: WorkflowSession) -> None:
        ctx = session.run_context

        doc = {
            "user_id": ctx.user_id,
            "run_id": ctx.run_id,
            "run_context": ctx.to_dict(),
            "metadata": session.metadata,
            "blueprint_spec": session.blueprint.model_dump(mode="json"),
            "graph_state": dict(session.graph_state),
        }

        self._col.replace_one(
            {"user_id": ctx.user_id, "run_id": ctx.run_id},
            doc,
            upsert=True
        )

    def load(self, run_id: str) -> WorkflowSession:
        doc = self._col.find_one({"run_id": run_id})
        if not doc:
            raise KeyError(f"No session for {run_id}")

        # 1) Rehydrate RunContext
        ctx = RunContext.from_dict(doc["run_context"])

        # 2) Re-create fresh session via factory
        session = self._factory.create(
            user_id=ctx.user_id,
            blueprint_spec=BlueprintSpec.model_validate(doc["blueprint_spec"]),
            metadata=doc.get("metadata", {}),
        )

        # 3) Override run_context (so we keep the same run_id, timestamps)
        session.run_context = ctx

        # 4) Restore GraphState in one shot
        session.graph_state = GraphState(**doc["graph_state"])

        return session

    def list_runs(self, user_id: str) -> List[str]:
        cursor = self._col.find({"user_id": user_id}, {"run_id": 1})
        return [d["run_id"] for d in cursor]
