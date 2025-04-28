from graph.graph_plan import GraphPlan, Step
from engine.base_graph_builder import BaseGraphBuilder

class GraphModifier:
    """
    Allows live/dynamic modification of an existing GraphPlan and recompilation.
    """

    def __init__(self, plan: GraphPlan, builder: BaseGraphBuilder):
        self.plan = plan
        self.builder = builder

    def add_step(self, name, func, after=None, condition=None, branches=None):
        """
        Adds a new step to the graph plan.
        """
        self.plan.add_step(name, func, after, condition, branches)

    def remove_step(self, name: str):
        """
        Removes a step from the graph plan.
        """
        self.plan.remove_step(name)

    def replace_step(self, name: str, new_func):
        """
        Replaces a step’s function but keeps its position.
        """
        step = self.plan.get_step(name)
        if not step:
            raise ValueError(f"Step '{name}' not found.")
        self.plan.replace_step(name, Step(name, new_func, step.after, step.condition, step.branches))

    def recompile_graph(self):
        """
        Recompile the updated graph plan into a new execution graph.
        """
        return self.builder.build(self.plan)
