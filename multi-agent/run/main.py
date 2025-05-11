from registry import element_registry
from session.repository.mongo_session_repository import MongoSessionRepository
from blueprints.loader.yaml_blueprint_loader import YAMLBlueprintLoader
from session.workflow_session_factory import WorkflowSessionFactory
from session.user_session_manager import UserSessionManager
from session.session_executor import SessionExecutor
from core.context import get_current_context


def setup_components():
    # auto‐discover all your node/tool/llm factories
    element_registry.auto_discover()

    # factory that builds fresh WorkflowSession
    session_factory = WorkflowSessionFactory(
        element_registry=element_registry,
        engine_name="langgraph"
    )

    # repository that stores / loads sessions from disk
    repository = MongoSessionRepository(session_factory=session_factory)

    # manager + executor
    manager = UserSessionManager(repository, session_factory)
    executor = SessionExecutor(manager, repository)

    return manager, executor


def main_new_session():
    manager, executor = setup_components()

    blueprint_loader = YAMLBlueprintLoader()
    spec = blueprint_loader.load("run/test_2_agents_1_merge.yml")

    session = manager.create_session(
        user_id="alice",
        blueprint_spec=spec,
        metadata={"experiment": "test-v1"}
    )

    run_id = session.run_context.run_id
    print(f"Started run: {run_id}")

    # manager, executor = setup_components()
    # — run it to completion —
    stream = executor.stream(
        session_or_id=session,
        inputs={"user_prompt": "eco the name"},
        stream_mode=["custom", "updates"]
    )
    for chunk in stream:
        if "custom" == chunk[0]:
            chunk = chunk[1]
            if chunk["type"] == "llm_token" and \
                    (chunk["node"] == "ask_llm_custom_agent_2" or chunk["node"] == "agent_merger_node"):
                print(chunk["chunk"], end="", flush=True)
    # print("Final GraphState:", final)


def main_resume_session(run_id: str):
    manager, executor = setup_components()

    # — resume an existing session —
    stream = executor.stream(
        session_or_id=run_id,
        inputs={"user_prompt": "eco the name"},
        stream_mode=["custom", "updates"]
    )
    for chunk in stream:
        if "custom" == chunk[0]:
            chunk = chunk[1]
            if chunk["type"] == "llm_token" and \
                    (chunk["node"] == "ask_llm_custom_agent_2" or chunk["node"] == "agent_merger_node"):
                print(chunk["chunk"], end="", flush=True)


if __name__ == "__main__":
    # main_new_session()
    # main_resume_session(get_current_context().run_id)
    main_resume_session("aaa07745-4d02-400c-8d88-c7ea75007bab")
