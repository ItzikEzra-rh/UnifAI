from run.main import setup_registry
from graph.blueprint_loader import BlueprintLoader
from engine.langgraph_builder import LangGraphBuilder

if __name__ == "__main__":
    registry = setup_registry()
    blueprint = BlueprintLoader(registry).build_from_code()
    graph = LangGraphBuilder().build(blueprint)

    state = {
        "user_input": "Summarize the Jira tickets from last sprint",
        "messages": [],
        "log": [],
    }

    result = graph.invoke(state)
    print("🧪 Test Result:\n", result)
from run.main import setup_registry
from graph.blueprint_loader import BlueprintLoader
from engine.langgraph_builder import LangGraphBuilder

if __name__ == "__main__":
    registry = setup_registry()
    blueprint = BlueprintLoader(registry).build_from_code()
    graph = LangGraphBuilder().build(blueprint)

    state = {
        "user_input": "Summarize the Jira tickets from last sprint",
        "messages": [],
        "log": [],
    }

    result = graph.invoke(state)
    print("🧪 Test Result:\n", result)
