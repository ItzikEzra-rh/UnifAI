from typing import List, Dict, Optional, Any, Callable
from schemas.blueprint.blueprint import StepMeta
from .step import Step


class GraphPlan:
    """
    Holds the abstract workflow: a (possibly cyclic) graph of Steps.

    Responsibilities:
      - Adding, removing, replacing steps
      - Querying step dependencies
      - Simple validations (unique uids, missing dependencies)
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
            uid: str,
            func: Any,
            after: Optional[List[str]] = None,
            exit_condition: Callable[[str], Callable[[Dict[str, Any]], Any]] = None,
            branches: Optional[Dict[str, str]] = None,
            metadata: Optional[StepMeta] = StepMeta(),
    ) -> None:
        """
        Add a new step or replace an existing one with the same uid.
        """
        if uid in self._index:
            raise ValueError(f"Step '{uid}' already exists in plan.")
        step = Step(uid, func, after, exit_condition, branches, metadata)
        self._steps.append(step)
        self._index[uid] = step

    def get_step(self, uid: str) -> Optional[Step]:
        """Return the Step by uid, or None if missing."""
        return self._index.get(uid)

    def remove_step(self, uid: str) -> None:
        """Remove a step by uid (and forget its index)."""
        step = self._index.pop(uid, None)
        if step:
            self._steps = [s for s in self._steps if s.uid != uid]

    def replace_step(self, new_step: Step) -> None:
        """
        Replace an existing step (matched by uid) with a new Step instance.
        """
        if new_step.uid not in self._index:
            raise KeyError(f"Step '{new_step.uid}' not found for replacement.")
        self.remove_step(new_step.uid)
        self._steps.append(new_step)
        self._index[new_step.uid] = new_step

    def validate(self) -> None:
        """
        Perform basic sanity checks:
          - All `after` references exist
          - All `branches` targets exist
          - No duplicate UIDs (enforced in add_step)
        Raises:
          ValueError if any problem found.
        """
        for step in self._steps:
            for dep in step.after:
                if dep not in self._index:
                    raise ValueError(f"Step '{step.uid}' depends on missing step '{dep}'.")
            for branch_target in step.branches.values():
                if branch_target not in self._index:
                    raise ValueError(f"Step '{step.uid}' branches to unknown step '{branch_target}'.")

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
        return [s for s in self._steps if s.uid not in dependents]

    def to_dict(self) -> Dict:
        """
        Serialize plan structure for introspection or persistence.
        """
        return {
            s.uid: {
                "after": s.after,
                "exit_condition": s.exit_condition,
                "branches": s.branches
            }
            for s in self._steps
        }

    def pretty_print(self) -> None:
        """
        Print out the plan as an ASCII tree, showing dependencies.
        If a node depends on multiple parents (e.g. agent_merger),
        it will be shown once, after all its parents.
        """
        roots = self.get_roots()
        visited = set()

        def _format_step(step, prefix, is_last):
            # Print the node
            bullet = "└── " if is_last else "├── "
            print(f"{prefix}{bullet}{step.uid}")
            # Avoid re-visiting
            if step.uid in visited:
                return
            visited.add(step.uid)

            # Recurse into its children (single-parent edges only)
            child_prefix = prefix + ("    " if is_last else "│   ")
            children = [
                s for s in self.steps
                # only those whose .after is exactly [step.uid] or includes it among multiple parents
                if s.after and step.uid in s.after
            ]
            # But skip any multi-parent nodes here; we’ll handle them at the parent level
            single_parent_children = [c for c in children if not c.after or len(c.after) == 1]
            for i, child in enumerate(single_parent_children):
                _format_step(child, child_prefix, i == len(single_parent_children) - 1)

        for root in roots:
            print(root.uid)
            visited.add(root.uid)

            # 1) print its single-parent children (agent_1, agent_2)
            direct = [
                s for s in self.steps
                if s.after and s.after == [root.uid]
            ]
            for i, child in enumerate(direct):
                _format_step(child, "", False)

            # 2) now find any merge nodes whose all parents are in `direct`
            direct_uids = {c.uid for c in direct}
            merges = [
                s for s in self.steps
                if s.after and len(s.after) > 1 and set(s.after) <= direct_uids
            ]
            if merges:
                # we assume just one merge for simplicity
                merge = merges[0]
                _format_step(merge, "", True)
