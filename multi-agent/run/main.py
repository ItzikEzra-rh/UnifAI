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
    active_session = session.create(blueprint_path="run/test_llm.yml")
    state = active_session.executable_graph.run({"user_prompt": "1"})
    print(state)
    # active_session.executable_graph.run(GraphState(user_prompt="1", messages=list()))

    # from langgraph.graph import StateGraph
    #
    # # ✅ 2. Define LangGraph steps using this state
    #
    # def step1(state: dict) -> dict:
    #     print("Step 1 sees:", state)
    #     state["output"] = "hello from step1"
    #     return state
    #
    # def step2(state: dict) -> dict:
    #     print(state["output"])
    #     state["user_prompt"] = "hiiii"
    #     print("Step 2 sees:", state)
    #     return state
    #
    # # ✅ 3. Build and run a simple LangGraph
    #
    # graph = StateGraph(dict)
    # graph.add_node("first", step1)
    # graph.add_node("second", step2)
    # graph.set_entry_point("first")
    # graph.add_edge("first", "second")
    # graph.set_finish_point("second")
    #
    # compiled = graph.compile()
    #
    # # ✅ 4. Run it with your initial state
    # initial_state = {"user_prompt": "hi"}
    # compiled.invoke(initial_state)


if __name__ == "__main__":
    main()
