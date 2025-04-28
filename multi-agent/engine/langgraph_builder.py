from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from graph.graph_plan import GraphPlan
from engine.base_graph_builder import BaseGraphBuilder


class LangGraphBuilder(BaseGraphBuilder):
    class State(TypedDict):
        messages: Annotated[list, add_messages]

    def __init__(self):
        self.graph = StateGraph(self.State)

    def add_node(self, name, func):
        self.graph.add_node(name, func)

    def add_edge(self, from_node, to_node):
        self.graph.add_edge(from_node, to_node)

    def add_conditional_edge(self, from_node, condition_fn, branches: dict):
        self.graph.add_conditional_edges(from_node, condition_fn, branches)

    def set_entry_point(self, name):
        self.graph.set_entry_point(name)

    def set_exit_point(self, name):
        self.graph.set_finish_point(name or END)

    def build(self, plan: GraphPlan):
        for step in plan.steps:
            self.add_node(step.name, step.func)
            if step.condition and step.branches:
                self.add_conditional_edge(step.name, step.condition, step.branches)
            elif step.after:
                self.add_edge(step.after, step.name)

        self.set_entry_point(plan.steps[0].name)
        self.set_exit_point(plan.steps[-1].name)
        return self.graph.compile()
