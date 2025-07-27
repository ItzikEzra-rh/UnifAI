from typing import Dict, List, Set
from graph.graph_plan import GraphPlan
from .models import PathValidation, DependencyMatrix
from .path_enumerator import PathEnumerator


class GraphValidator:
    """Validates channel dependencies in graph structures."""

    def validate_path(self, path_steps: List[str], plan: GraphPlan, matrix: DependencyMatrix) -> PathValidation:
        """Validate a single execution path."""
        # REUSE existing logic from PathValidator.validate_path() - copy exactly
        produced = matrix.external_channels.copy()
        missing_channels = {}
        impossible_channels = {}

        for step_id in path_steps:
            step = plan.get_step(step_id)
            if not step:
                continue

            required = step.total_reads()
            missing = required - produced

            if missing:
                impossible = {ch for ch in missing if not matrix.can_produce(ch)}
                possible = missing - impossible

                if possible:
                    missing_channels[step_id] = possible
                if impossible:
                    impossible_channels[step_id] = impossible

            produced.update(step.writes)

        is_valid = len(impossible_channels) == 0 and len(missing_channels) == 0
        return PathValidation(
            path_id=f"path_{'_'.join(path_steps[:2])}",
            steps=path_steps,
            missing_channels=missing_channels,
            impossible_channels=impossible_channels,
            is_valid=is_valid
        )

    def validate_all_paths(self, plan: GraphPlan, matrix: DependencyMatrix) -> Dict[str, PathValidation]:
        """Validate all paths in the graph."""
        # REUSE existing logic from service.py lines 24-28
        enumerator = PathEnumerator()
        paths = enumerator.enumerate_paths(plan)

        return {
            path_id: self.validate_path(steps, plan, matrix)
            for path_id, steps in paths.items()
        }

    def find_missing_inputs(self, plan: GraphPlan, matrix: DependencyMatrix) -> Set[str]:
        """Find all channels that current plan needs but doesn't have."""
        all_missing: Set[str] = set()
        available: Set[str] = matrix.external_channels.copy()

        # Add all outputs from existing steps
        for step in plan.steps:
            available.update(step.writes)  # step.writes is Set[str]

        # Find what's missing across all steps
        for step in plan.steps:
            required: Set[str] = step.total_reads()  # This returns Set[str]
            missing: Set[str] = required - available  # Set[str] - Set[str] = Set[str]

            # Only include channels that CAN be produced (not impossible)
            for channel in missing:
                if matrix.can_produce(channel):
                    all_missing.add(channel)  # Add individual strings, not sets

        return all_missing
