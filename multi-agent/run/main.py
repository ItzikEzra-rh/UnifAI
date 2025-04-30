import os, yaml, uuid
# from registry.component_registry import ComponentRegistry
# from plugins.plugin_registry import PluginRegistry
# from graph.blueprint_loader import BlueprintLoader
# from composers.plan_composer import PlanComposer
# from engine.engine_factory import EngineFactory
# from run.run_loop import LoopExecutor
# from state.runtime_state import RuntimeState
# from logs.in_memory_logger import InMemoryLogger
from registry import element_registry
from blueprints.loader.yaml_blueprint_loader import YAMLBlueprintLoader
from session.workflow_session_factory import WorkflowSessionFactory


def main():
    element_registry.auto_discover()

    session = WorkflowSessionFactory(element_registry=element_registry,
                                     blueprint_loader=YAMLBlueprintLoader(),
                                     plan_composer=None,
                                     engine_factory=None,
                                     logger_factory=None)
    session.create(blueprint_path="run/test_mock_agent.yml")


if __name__ == "__main__":
    main()
