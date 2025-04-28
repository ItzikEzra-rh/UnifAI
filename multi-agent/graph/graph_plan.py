from typing import List
from graph.step import Step


class GraphPlan:
    def __init__(self):
        self.steps: List[Step] = []

    def add_step(self, name, func, after=None, condition=None, branches=None):
        self.steps.append(Step(name, func, after, condition, branches))

    def get_step(self, name):
        return next((s for s in self.steps if s.name == name), None)

    def remove_step(self, name):
        self.steps = [s for s in self.steps if s.name != name]

    def replace_step(self, name, new_step: Step):
        self.remove_step(name)
        self.steps.append(new_step)
