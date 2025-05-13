from registry import element_registry
from session.repository.mongo_session_repository import MongoSessionRepository
from blueprints.loader.yaml_blueprint_loader import YAMLBlueprintLoader
from session.workflow_session_factory import WorkflowSessionFactory
from session.user_session_manager import UserSessionManager
from session.session_executor import SessionExecutor
from core.context import get_current_context

import sys
import textwrap
from typing import Iterator, Any, Dict


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def render(buffers: Dict[str, str], width: int = 60):
    """
    Draw one wrapped box per node in the order first seen.
    Each box grows downward as new tokens arrive, with wrapping.
    """
    clear_screen()
    for node, text in buffers.items():
        title = f"[{node}]"
        # top border
        print("┌" + "─" * width + "┐")
        # title line
        print("│ " + title.ljust(width - 1) + "│")
        # separator
        print("├" + "─" * width + "┤")
        # wrap the buffer into lines no longer than `width - 1`
        wrapped = textwrap.wrap(text, width=width - 1) or [""]
        for line in wrapped:
            print("│ " + line.ljust(width - 1) + "│")
        # bottom border + blank line
        print("└" + "─" * width + "┘\n")


def stream_boxes(stream: Iterator[Any], width: int = 60):
    """
    Consume an LLM‐style custom stream, buffer each node’s tokens,
    and re-render wrapped boxes on every token arrival.
    """
    buffers: Dict[str, str] = {}

    for raw in stream:
        # 1) filter down to your custom payloads
        if raw[0] != "custom":
            continue

        chunk = raw[1]
        # 2) only care about LLM tokens
        if chunk.get("type") != "llm_token":
            continue

        node = chunk.get("node", "unknown")
        token = chunk.get("chunk", "")

        # 3) initialize buffer if first time
        buffers.setdefault(node, "")

        # 4) append incoming token
        buffers[node] += token

        # 5) redraw all boxes
        render(buffers, width=width)

    # final newline so the cursor isn’t stuck
    print()


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
        inputs={"user_prompt": "what is the tm command?"},
        stream_mode=["custom"]
    )
    stream_boxes(stream)
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
