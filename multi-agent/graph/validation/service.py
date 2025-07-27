from typing import Dict, List, Set
from catalog.element_registry import ElementRegistry
from graph.graph_plan import GraphPlan
from .models import ValidationResult, ValidationStatus, NodeSuggestion
from .matrix_builder import MatrixBuilder
from .graph_validator import GraphValidator
from .node_suggester import NodeSuggester


class GraphValidationService:
    """Coordinates validation and suggestions for graph building."""

    def __init__(self, element_registry: ElementRegistry):
        self._matrix = MatrixBuilder(element_registry).build()
        self._validator = GraphValidator()
        self._suggester = NodeSuggester()

    def validate(self, plan: GraphPlan) -> ValidationResult:
        """Validate complete graph plan."""
        path_validations = self._validator.validate_all_paths(plan, self._matrix)

        all_errors = []
        all_warnings = []

        for validation in path_validations.values():
            for step_id, channels in validation.impossible_channels.items():
                all_errors.append(f"Step '{step_id}' requires impossible channels: {channels}")

            for step_id, channels in validation.missing_channels.items():
                all_warnings.append(f"Step '{step_id}' missing upstream channels: {channels}")

        return ValidationResult(
            is_valid=all(pv.is_valid for pv in path_validations.values()),
            path_validations=path_validations,
            errors=all_errors,
            warnings=all_warnings
        )

    def suggest_next_nodes(self, current_plan: GraphPlan) -> List[NodeSuggestion]:
        """
        THE core method: suggest useful nodes to add to current plan.
        Coordinates validator + suggester.
        """
        # 1. Find what channels are missing using validator
        missing_channels = self._validator.find_missing_inputs(current_plan, self._matrix)

        # 2. Get suggestions using suggester
        return self._suggester.suggest_for_channels(missing_channels, self._matrix)
