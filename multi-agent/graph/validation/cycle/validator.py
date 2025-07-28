from graph.graph_plan import GraphPlan
from ..validator import Validator
from ..models import ValidationReport
from .detector import CycleDetector


class CycleValidator(Validator):
    """Validates graph for execution cycles."""

    def __init__(self, *args, **kwargs):
        self._detector = CycleDetector()

    def validate(self, plan: GraphPlan) -> ValidationReport:
        cycles, messages = self._detector.detect_cycles(plan)
        
        return ValidationReport(
            validator_name=self.name,
            is_valid=len(cycles) == 0,
            messages=messages,
            details={"cycles": [cycle.model_dump() for cycle in cycles]}
        ) 