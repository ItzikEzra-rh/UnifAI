from graph.graph_plan import GraphPlan
from ..validator import Validator
from ..models import ValidationReport
from .checker import DependencyChecker


class DependencyValidator(Validator):
    """Validates step dependencies and branch targets."""

    def __init__(self, *args, **kwargs):
        self._checker = DependencyChecker()

    def validate(self, plan: GraphPlan) -> ValidationReport:
        issues, messages = self._checker.check_dependencies(plan)
        
        return ValidationReport(
            validator_name=self.name,
            is_valid=len(issues) == 0,
            messages=messages,
            details={"dependency_issues": [issue.model_dump() for issue in issues]}
        )
