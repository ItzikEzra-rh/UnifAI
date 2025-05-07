from registry import element_registry
from blueprints.loader.yaml_blueprint_loader import YAMLBlueprintLoader
from session.workflow_session_factory import WorkflowSessionFactory
from runtime.state.graph_state import GraphState


def main():
    element_registry.auto_discover()

    session = WorkflowSessionFactory(element_registry=element_registry,
                                     blueprint_loader=YAMLBlueprintLoader(),
                                     engine_name="langgraph",
                                     logger_factory=None)
    active_session = session.create(blueprint_path="run/test_2_agents_1_merge.yml")
    # active_session = session.create(blueprint_path="run/test_mock_agent.yml")
    # state = active_session.executable_graph.run({"user_prompt": "echo the name."})
    # print(state)
    for chunk in active_session.executable_graph.stream({"user_prompt": "explain the name."},
                                                        stream_mode=["custom", "updates"]):
        print(chunk)
        break
        # if chunk["type"] == "llm_token" and \
        #         (chunk["node"] == "ask_llm_custom_agent_2" or chunk["node"] == "agent_merger_node"):
        #     print(chunk["chunk"], end="", flush=True)


if __name__ == "__main__":
    main()
