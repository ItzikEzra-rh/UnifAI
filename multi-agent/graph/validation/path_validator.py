from typing import Dict, List, Set
from graph.graph_plan import GraphPlan
from .models import PathValidation, DependencyMatrix


class PathValidator:
    """Validates individual execution paths."""

    def validate_path(self,
                      path_steps: List[str],
                      plan: GraphPlan,
                      matrix: DependencyMatrix) -> PathValidation:
        """Validate a single execution path."""
        produced = matrix.external_channels.copy()
        missing_channels = {}
        impossible_channels = {}

        for step_id in path_steps:
            step = plan.get_step(step_id)
            if not step:
                continue

            # Check missing channels
            required = step.total_reads()
            missing = required - produced

            if missing:
                # Categorize missing channels
                impossible = {ch for ch in missing if not matrix.can_produce(ch)}
                possible = missing - impossible

                if possible:
                    missing_channels[step_id] = possible
                if impossible:
                    impossible_channels[step_id] = impossible

            # Add produced channels
            produced.update(step.writes)

        return PathValidation(
            path_id=f"path_{'_'.join(path_steps[:2])}",
            steps=path_steps,
            missing_channels=missing_channels,
            impossible_channels=impossible_channels
        )
