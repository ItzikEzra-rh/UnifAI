from typing import Dict, List, Set, Optional
from catalog.element_registry import ElementRegistry
from graph.graph_plan import GraphPlan
from .models import ValidationResult, ValidationStatus, DependencyMatrix
from .matrix_builder import MatrixBuilder
from .path_enumerator import PathEnumerator
from .path_validator import PathValidator


class GraphValidationService:
    """
    Clean validation service for GraphPlan.
    Single responsibility: validate graph channel dependencies.
    """

    def __init__(self, element_registry: ElementRegistry):
        self._matrix = MatrixBuilder(element_registry).build()
        self._path_enumerator = PathEnumerator()
        self._path_validator = PathValidator()

    def validate(self, plan: GraphPlan) -> ValidationResult:
        """Validate complete graph plan."""
        # Enumerate all execution paths
        paths = self._path_enumerator.enumerate_paths(plan)

        # Validate each path
        path_validations = {}
        all_errors = []
        all_warnings = []

        for path_id, path_steps in paths.items():
            validation = self._path_validator.validate_path(path_steps, plan, self._matrix)
            path_validations[path_id] = validation

            # Collect errors and warnings
            for step_id, channels in validation.impossible_channels.items():
                all_errors.append(
                    f"Step '{step_id}' requires impossible channels: {channels}"
                )

            for step_id, channels in validation.missing_channels.items():
                all_warnings.append(
                    f"Step '{step_id}' missing upstream channels: {channels}"
                )

        is_valid = all(pv.is_valid for pv in path_validations.values())

        return ValidationResult(
            is_valid=is_valid,
            path_validations=path_validations,
            errors=all_errors,
            warnings=all_warnings
        )

    def validate_edge(self,
                      from_step_id: str,
                      to_step_id: str,
                      current_plan: GraphPlan,
                      current_produced: Set[str]) -> ValidationStatus:
        """
        Validate a single edge for UI feedback.
        Returns: OK (green), WARNING (yellow), or ERROR (red).
        """
        from_step = current_plan.get_step(from_step_id)
        to_step = current_plan.get_step(to_step_id)

        if not from_step or not to_step:
            return ValidationStatus.ERROR

        # Calculate what would be available
        available = current_produced | from_step.writes | self._matrix.external_channels
        missing = to_step.total_reads() - available

        if not missing:
            return ValidationStatus.OK

        # Check if missing channels are possible
        impossible = {ch for ch in missing if not self._matrix.can_produce(ch)}

        return ValidationStatus.ERROR if impossible else ValidationStatus.WARNING

    def suggest_producers(self, channel: str) -> List[Dict[str, str]]:
        """Suggest elements that can produce a missing channel."""
        suggestions = []

        if channel in self._matrix.external_channels:
            suggestions.append({
                "type": "external",
                "message": f"'{channel}' is provided externally"
            })

        if channel in self._matrix.producer_map:
            for category, type_key in self._matrix.producer_map[channel]:
                suggestions.append({
                    "type": "element",
                    "category": category,
                    "type_key": type_key,
                    "message": f"Add {type_key} ({category})"
                })

        return suggestions

    def get_missing_channels(self, plan: GraphPlan) -> Dict[str, Set[str]]:
        """Get all missing channels across all paths."""
        result = self.validate(plan)
        missing_by_step = {}

        for path_validation in result.path_validations.values():
            for step_id, channels in path_validation.missing_channels.items():
                missing_by_step.setdefault(step_id, set()).update(channels)

        return missing_by_step
