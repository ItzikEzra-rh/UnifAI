from graph.graph_plan import GraphPlan
from ..base import Validator, ValidationReport, ValidationMessage, MessageSeverity
from .models import StructuralValidationDetails
from .dependency_checker import DependencyChecker
from .cycle_detector import CycleDetector
from .orphan_detector import OrphanDetector


class StructuralValidator(Validator):
    """Orchestrates structural validation checks."""
    
    def __init__(self):
        self._dependency_checker = DependencyChecker()
        self._cycle_detector = CycleDetector()
        self._orphan_detector = OrphanDetector()
    
    @property
    def name(self) -> str:
        return "structural"
    
    def validate(self, plan: GraphPlan) -> ValidationReport:
        """Validate graph structural integrity."""
        all_messages = []
        
        # Check dependencies and branches
        dependency_issues, dep_messages = self._dependency_checker.check_dependencies(plan)
        all_messages.extend(dep_messages)
        
        # Detect cycles
        cycles, cycle_messages = self._cycle_detector.detect_cycles(plan)
        all_messages.extend(cycle_messages)
        
        # Find orphaned steps
        orphaned_steps, orphan_messages = self._orphan_detector.detect_orphans(plan)
        all_messages.extend(orphan_messages)
        
        # Determine overall validity
        is_valid = not dependency_issues and not cycles and not orphaned_steps
        
        # Create detailed results
        details = StructuralValidationDetails(
            dependency_issues=dependency_issues,
            cycles=cycles,
            orphaned_steps=orphaned_steps
        )
        
        return ValidationReport(
            validator_name=self.name,
            is_valid=is_valid,
            messages=all_messages,
            details=details
        )
 