from typing import List
from catalog.element_registry import ElementRegistry
from graph.graph_plan import GraphPlan
from .base import ValidationReport
from .models import ValidationResult
from .connectors.models import PathSuggestion
from .connectors.validator import ConnectorValidator
from .connectors.matrix_builder import MatrixBuilder
from .structural.validator import StructuralValidator
from .semantic.validator import RequiredNodesValidator
from .settings import ValidationSettings


class GraphValidationService:
    """Orchestrates all graph validators."""

    def __init__(self, element_registry: ElementRegistry):
        # Build matrix once and inject it
        matrix = MatrixBuilder(element_registry).build()

        # Initialize all validators directly
        self._connector_validator = ConnectorValidator(matrix)
        self._structural_validator = StructuralValidator()

        # Load validation settings (env-configurable)
        val_settings = ValidationSettings()

        self._semantic_validator = RequiredNodesValidator(
            required_start_nodes=val_settings.required_start_nodes,
            required_end_nodes=val_settings.required_end_nodes,
            required_any_nodes=val_settings.required_any_nodes,
        )

    def validate_all(self, plan: GraphPlan) -> ValidationResult:
        """Run all validators and return complete result."""
        connector_report = self._connector_validator.validate(plan)
        structural_report = self._structural_validator.validate(plan)
        semantic_report = self._semantic_validator.validate(plan)

        is_valid = all([
            connector_report.is_valid,
            structural_report.is_valid,
            semantic_report.is_valid
        ])

        return ValidationResult(
            is_valid=is_valid,
            connector_report=connector_report,
            structural_report=structural_report,
            semantic_report=semantic_report
        )

    def validate_connectors(self, plan: GraphPlan) -> ValidationReport:
        """Run only connector validation."""
        return self._connector_validator.validate(plan)

    def validate_structure(self, plan: GraphPlan) -> ValidationReport:
        """Run only structural validation."""
        return self._structural_validator.validate(plan)

    def validate_semantics(self, plan: GraphPlan) -> ValidationReport:
        """Run only semantic validation."""
        return self._semantic_validator.validate(plan)

    def suggest_fixes(self, plan: GraphPlan) -> List[PathSuggestion]:
        """Get node suggestions from connector validator."""
        return self._connector_validator.suggest_fixes(plan)
