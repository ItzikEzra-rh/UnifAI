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


def main():
    element_registry.auto_discover()
    # print(element_registry.list_elements())

    # Load blueprint
    blueprint_dict = YAMLBlueprintLoader().load("run/test_mock_agent.yml")
    print(blueprint_dict)
    #  Plugin registry & factories
    # plugin_registry = PluginRegistry()

    # Load & validate blueprint
    # loader = BlueprintLoader(plugin_registry)
    # blueprint = loader.load_blueprint(blueprint_dict)

    # Compose the GraphPlan
    # ctx = loader.build_context()  # holds both registries + logger
    # composer = PlanComposer(ctx)
    # for step in blueprint.plan:
    #     composer.add_step(step)

    #  Compile to executable graph
    # builder = EngineFactory.get_builder("langgraph")
    # compiled_graph = builder.build(composer.plan)

    #  Wrap in RuntimeState
    # logger = InMemoryLogger()
    # metadata = {"run_id": str(uuid.uuid4())}
    # runtime = RuntimeState(compiled_graph, composer.plan, logger, metadata)

    #  Execute
    # initial_state = {"user_input": "Hello, mock agent!"}
    # final_state = LoopExecutor.execute_until_exit(runtime, initial_state)

    #  Inspect & persist
    # print("Events:", logger.get_events())
    # runtime.save("last_run.json")
    # print("Final answer:", final_state.get("final_output"))


if __name__ == "__main__":
    main()
