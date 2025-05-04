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
    active_session = session.create(blueprint_path="run/test_mock_agent.yml")
    active_session.executable_graph.run(GraphState(input="hi"))


if __name__ == "__main__":
    main()
