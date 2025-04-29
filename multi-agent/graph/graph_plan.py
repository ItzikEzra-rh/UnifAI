from typing import List, Dict, Optional, Any
from .step import Step


class GraphPlan:
    """
    Holds the abstract workflow: a (possibly cyclic) graph of Steps.

    Responsibilities:
      - Adding, removing, replacing steps
      - Querying step dependencies
      - Simple validations (unique names, missing dependencies)
    """

    def __init__(self) -> None:
        # preserve insertion order for deterministic builds
        self._steps: List[Step] = []
        self._index: Dict[str, Step] = {}

    @property
    def steps(self) -> List[Step]:
        """Ordered list of steps."""
        return list(self._steps)

    def add_step(
            self,
            name: str,
            func: Any,
            after: Optional[List[str]] = None,
            exit_condition: Optional[str] = None,
            branches: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Add a new step or replace an existing one with the same name.
        """
        if name in self._index:
            raise ValueError(f"Step '{name}' already exists in plan.")
        step = Step(name, func, after, exit_condition, branches)
        self._steps.append(step)
        self._index[name] = step

    def get_step(self, name: str) -> Optional[Step]:
        """Return the Step by name, or None if missing."""
        return self._index.get(name)

    def remove_step(self, name: str) -> None:
        """Remove a step by name (and forget its index)."""
        step = self._index.pop(name, None)
        if step:
            self._steps = [s for s in self._steps if s.name != name]

    def replace_step(self, new_step: Step) -> None:
        """
        Replace an existing step (matched by name) with a new Step instance.
        """
        if new_step.name not in self._index:
            raise KeyError(f"Step '{new_step.name}' not found for replacement.")
        self.remove_step(new_step.name)
        self._steps.append(new_step)
        self._index[new_step.name] = new_step

    def validate(self) -> None:
        """
        Perform basic sanity checks:
          - All `after` references exist
          - All `branches` targets exist
          - No duplicate names (enforced in add_step)
        Raises:
          ValueError if any problem found.
        """
        for step in self._steps:
            for dep in step.after:
                if dep not in self._index:
                    raise ValueError(f"Step '{step.name}' depends on missing step '{dep}'.")
            for branch_target in step.branches.values():
                if branch_target not in self._index:
                    raise ValueError(f"Step '{step.name}' branches to unknown step '{branch_target}'.")

    def get_roots(self) -> List[Step]:
        """
        Return steps that have no dependencies (no 'after').
        """
        return [s for s in self._steps if not s.after]

    def get_leaves(self) -> List[Step]:
        """
        Return steps that nothing depends on (no other step lists them in 'after').
        """
        dependents = {dep for s in self._steps for dep in s.after}
        return [s for s in self._steps if s.name not in dependents]

    def to_dict(self) -> Dict:
        """
        Serialize plan structure for introspection or persistence.
        """
        return {
            s.name: {
                "after": s.after,
                "exit_condition": s.exit_condition,
                "branches": s.branches
            }
            for s in self._steps
        }
