from typing import List, Optional
from catalog.element_registry import ElementRegistry
from graph.graph_plan import GraphPlan
from .validator import Validator
from .models import ValidationReport, ValidationResult
from .settings import ValidationSettings


class GraphValidationService:
    """Orchestrates all graph validators."""

    def __init__(self, element_registry: ElementRegistry, settings: ValidationSettings = None):
        self._validators = self._create_validators(
            element_registry=element_registry,
            settings=settings or ValidationSettings()
        )

    def _create_validators(self, *args, **kwargs) -> List[Validator]:
        """Create all registered validators with provided dependencies."""
        return [
            validator_class(*args, **kwargs)
            for validator_class in Validator.get_all_validators()
        ]

    def validate_all(self, plan: GraphPlan) -> ValidationResult:
        """Run all validators and return aggregate result."""
        reports = [validator.validate(plan) for validator in self._validators]
        is_valid = all(report.is_valid for report in reports)
        
        return ValidationResult(
            is_valid=is_valid,
            reports=reports
        )

    def get_validator(self, name: str) -> Optional[Validator]:
        """Get validator by name."""
        return next((v for v in self._validators if v.name == name), None)

    def run_validator(self, name: str, plan: GraphPlan) -> ValidationReport:
        """Run specific validator by name."""
        validator = self.get_validator(name)
        if not validator:
            raise ValueError(f"Validator '{name}' not found")
        return validator.validate(plan)

    # Convenience methods for backward compatibility
    def validate_dependencies(self, plan: GraphPlan) -> ValidationReport:
        return self.run_validator('dependency', plan)
    
    def validate_cycles(self, plan: GraphPlan) -> ValidationReport:
        return self.run_validator('cycle', plan)
    
    def validate_orphans(self, plan: GraphPlan) -> ValidationReport:
        return self.run_validator('orphan', plan)
    
    def validate_channels(self, plan: GraphPlan) -> ValidationReport:
        return self.run_validator('channel', plan)

    def suggest_fixes(self, plan: GraphPlan) -> List:
        """Get fix suggestions from validators that support it."""
        suggestions = []
        
        for validator in self._validators:
            if hasattr(validator, 'suggest_fixes'):
                suggestions.extend(validator.suggest_fixes(plan))
        
        return suggestions
