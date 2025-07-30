from typing import Set, List
from graph.graph_plan import GraphPlan
from ..models import ValidationMessage, MessageSeverity, MessageCode
from .models import PathValidation, DependencyMatrix, PathSuggestion, ChannelValidationDetails, ChannelSummary
from .path_enumerator import PathEnumerator
from .node_suggester import NodeSuggester


class ChannelAnalyzer:
    """Validates channel/data flow connections between nodes."""

    def __init__(self, matrix: DependencyMatrix):
        self._matrix = matrix
        self._enumerator = PathEnumerator()
        self._suggester = NodeSuggester()

    def analyze(self, plan: GraphPlan) -> tuple[ChannelValidationDetails, List[ValidationMessage]]:
        """Validate channel dependencies across all paths."""
        messages = []
        path_validations = {}
        all_missing = set()
        all_impossible = set()

        paths = self._enumerator.enumerate_paths(plan)

        for path_id, steps in paths.items():
            path_validation = self._validate_single_path(path_id, steps, plan)
            path_validations[path_id] = path_validation

            # Collect summary data
            for step_channels in path_validation.missing_channels.values():
                all_missing.update(step_channels)

            for step_channels in path_validation.impossible_channels.values():
                all_impossible.update(step_channels)

            # Create messages
            for step_id, channels in path_validation.impossible_channels.items():
                messages.append(ValidationMessage(
                    text=f"Step '{step_id}' requires impossible channels: {channels}",
                    severity=MessageSeverity.ERROR,
                    code=MessageCode.IMPOSSIBLE_CHANNELS,
                    context={
                        "step_id": step_id,
                        "channels": list(channels),
                        "path_id": path_id
                    }
                ))

            for step_id, channels in path_validation.missing_channels.items():
                messages.append(ValidationMessage(
                    text=f"Step '{step_id}' missing upstream channels: {channels}",
                    severity=MessageSeverity.WARNING,
                    code=MessageCode.MISSING_CHANNELS,
                    context={
                        "step_id": step_id,
                        "channels": list(channels),
                        "path_id": path_id
                    }
                ))

        # Create typed details
        details = ChannelValidationDetails(
            path_validations=path_validations,
            summary=ChannelSummary(
                missing=all_missing,
                impossible=all_impossible
            )
        )

        return details, messages

    def _validate_single_path(self, path_id: str, steps: List[str], plan: GraphPlan) -> PathValidation:
        """Validate single path - reuse existing logic."""
        produced = self._matrix.external_channels.copy()
        missing_channels = {}
        impossible_channels = {}

        for step_id in steps:
            step = plan.get_step(step_id)
            if not step:
                continue

            required = step.total_reads()
            upstream_required = required - step.writes  # Channels needed from upstream steps
            missing = upstream_required - produced

            if missing:
                impossible = {ch for ch in missing if not self._matrix.can_produce(ch)}
                possible = missing - impossible

                if possible:
                    missing_channels[step_id] = possible
                if impossible:
                    impossible_channels[step_id] = impossible

            produced.update(step.total_writes())

        is_valid = len(impossible_channels) == 0 and len(missing_channels) == 0
        return PathValidation(
            path_id=path_id,
            steps=steps,
            missing_channels=missing_channels,
            impossible_channels=impossible_channels,
            is_valid=is_valid
        )

    def suggest_fixes(self, plan: GraphPlan) -> List[PathSuggestion]:
        """Suggest nodes to fix connector issues, organized by path."""
        # Run validation to get detailed path analysis
        details, _ = self.analyze(plan)

        path_suggestions = []

        for path_validation in details.invalid_paths.values():
            # Collect all missing channels for this path
            all_missing_for_path = set()
            for missing_channels_set in path_validation.missing_channels.values():
                all_missing_for_path.update(missing_channels_set)

            # Generate suggestions for this path's missing channels
            if all_missing_for_path:
                suggestions = self._suggester.suggest_for_channels(all_missing_for_path, self._matrix)
                path_suggestions.append(PathSuggestion(
                    path_id=path_validation.path_id,
                    missing_channels=all_missing_for_path,
                    suggestions=suggestions
                ))

        return path_suggestions 