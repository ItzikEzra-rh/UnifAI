from abc import ABC, abstractmethod
from typing import Any, Callable, Dict
from graph.graph_plan import GraphPlan, Step


class BaseGraphBuilder(ABC):
    """
    Abstract interface for any graph execution engine.

    Subclasses must implement node/edge wiring and entry/exit.
    """

    @abstractmethod
    def add_node(self, name: str, func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """
        Register a node in the engine under `name` with its execution function.
        """
        ...

    @abstractmethod
    def add_edge(self, from_node: str, to_node: str) -> None:
        """
        Add an unconditional edge: from_node → to_node.
        """
        ...

    @abstractmethod
    def add_conditional_edge(
            self,
            from_node: str,
            condition: Callable[[Dict[str, Any]], Any],
            branches: Dict[Any, str]
    ) -> None:
        """
        Add one or more edges out of `from_node` guarded by `condition`.
        `branches` maps condition-output → next‐node name.
        """
        ...

    @abstractmethod
    def set_entry(self, name: str) -> None:
        """
        Mark `name` as the graph’s entry point.
        """
        ...

    @abstractmethod
    def set_exit(self, name: str) -> None:
        """
        Mark `name` as the graph’s exit / finish point.
        """
        ...

    @abstractmethod
    def build(self) -> Any:
        """
        Compile and return the engine’s executable graph object.
        """
        ...

    def compile_from_plan(
            self,
            plan: GraphPlan) -> Any:
        """
        Default helper: wires up all steps, dependencies, conditionals,
        and identifies entry/exit, then builds.
        """
        # 1) add every node
        for step in plan.steps:
            self.add_node(step.name, step.func)

        # 2) add dependencies and conditionals
        for step in plan.steps:
            # unconditional dependencies
            for dep in step.after:
                self.add_edge(dep, step.name)

            # conditional branches (cycles or forks)
            if step.exit_condition and step.branches:
                self.add_conditional_edge(step.name, step.exit_condition, step.branches)

        # 3) pick a single entry & exit (you could relax to multiple)
        roots = plan.get_roots()
        leaves = plan.get_leaves()
        if not roots:
            raise ValueError("Plan has no root steps.")
        if not leaves:
            raise ValueError("Plan has no leaf steps.")
        self.set_entry(roots[0].name)
        self.set_exit(leaves[0].name)

        # 4) compile
        return self.build()
