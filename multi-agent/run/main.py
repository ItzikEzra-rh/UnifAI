from registry import element_registry
from session.repository.mongo_session_repository import MongoSessionRepository
from blueprints.loader.yaml_blueprint_loader import YAMLBlueprintLoader
from session.workflow_session_factory import WorkflowSessionFactory
from session.user_session_manager import UserSessionManager
from session.session_executor import SessionExecutor
from core.context import get_current_context

from typing import Iterator, Any, Dict, List
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console

console = Console()


def make_layout(buffers: Dict[str, str], logs: List[str]) -> Layout:
    layout = Layout()

    # Top pane for logs
    layout.split_column(
        Layout(name="logs", size=len(logs) + 2),
        Layout(name="agents", ratio=1),
    )
    layout["logs"].update(Panel("\n".join(logs), title="Agents Stream"))

    # Bottom pane: one panel per agent, in order seen
    agent_panels = []
    for node, text in buffers.items():
        agent_panels.append(Panel(text or "[waiting…]", title=node, expand=True))
    # split row into as many columns as there are agents
    layout["agents"].split_row(*agent_panels)
    return layout


def stream_with_rich(
        stream: Iterator[Any],
        initial_logs: List[str] = None,
):
    logs = initial_logs[:] if initial_logs else []
    buffers: Dict[str, str] = {}

    with Live(make_layout(buffers, logs), console=console, refresh_per_second=10) as live:
        for raw in stream:
            # your filtering logic
            if raw[0] != "custom":
                continue
            chunk = raw[1]
            if chunk.get("type") != "llm_token":
                continue

            node = chunk.get("node", "unknown")
            token = chunk.get("chunk", "")

            buffers.setdefault(node, "")
            buffers[node] += token

            # update the layout in-place
            live.update(make_layout(buffers, logs))


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
    spec = blueprint_loader.load("run/test_2_agents_slack_docs_merger.yml")
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
        inputs={"user_prompt": "what is the tm command and tell me from where do you get your info about it?"},
        stream_mode=["custom"]
    )
    stream_with_rich(stream)
    # for chunk in stream:
    #     if "custom" == chunk[0]:
    #         chunk = chunk[1]
    #         if chunk["type"] == "llm_token" and \
    #                 (chunk["node"] == "slack_agent_node" or chunk["node"] == "agent_merger_node"):
    #             print(chunk["chunk"], end="", flush=True)


def main_resume_session(run_id: str):
    manager, executor = setup_components()

    # — resume an existing session —
    stream = executor.stream(
        session_or_id=run_id,
        inputs={"user_prompt": "eco the name"},
        stream_mode=["custom", "updates"]
    )
    for chunk in stream:
        print(chunk)
        if "custom" == chunk[0]:
            chunk = chunk[1]
            if chunk["type"] == "llm_token" and \
                    (chunk["node"] == "ask_llm_custom_agent_2" or chunk["node"] == "agent_merger_node"):
                print(chunk["chunk"], end="", flush=True)


if __name__ == "__main__":
    main_new_session()
    # main_resume_session(get_current_context().run_id)
    # main_resume_session("8241065f-e3f1-4735-9630-233775a70dcb")
