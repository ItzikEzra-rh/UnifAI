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

    def pretty_print(self) -> None:
        """
        Print out the plan as an ASCII tree, showing dependencies,
        exit conditions and branch targets.  Detects cycles and
        annotates already‐visited nodes.
        """
        roots = self.get_roots()
        visited = set()

        def _format_step(step, prefix, is_last):
            """Print one step, then recurse into its children."""
            # Detect cycle
            marker = " [*]" if step.name in visited else ""
            # Mark visited once we print it
            if step.name not in visited:
                visited.add(step.name)

            # Build detail suffix
            details = []
            if step.exit_condition:
                details.append(f"exit_if={step.exit_condition}")
            if step.branches:
                b = ", ".join(f"{c}→{t}" for c, t in step.branches.items())
                details.append(f"branches={b}")
            suffix = (" [" + "; ".join(details) + "]") if details else ""

            # Print the node line
            bullet = "└── " if is_last else "├── "
            print(f"{prefix}{bullet}{step.name}{suffix}{marker}")

            # Compute new prefix for children
            child_prefix = prefix + ("    " if is_last else "│   ")
            # Find direct children (those that list this step in .after)
            children = [s for s in self.steps if step.name in (s.after or [])]
            for i, child in enumerate(children):
                _format_step(child, child_prefix, i == len(children) - 1)

        # If no explicit roots (fully cyclic), fall back to printing all steps flat
        if not roots:
            print("No roots found (graph may be fully cyclic). Listing all steps:")
            roots = self.steps

        # Kick off the walk
        for i, root in enumerate(roots):
            # For each root we don’t indent
            print(root.name)
            visited.add(root.name)
            children = [s for s in self.steps if root.name in (s.after or [])]
            for j, child in enumerate(children):
                _format_step(child, "", j == len(children) - 1)
