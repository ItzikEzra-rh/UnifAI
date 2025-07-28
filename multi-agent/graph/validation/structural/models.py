from typing import List, Set
from pydantic import BaseModel, Field, ConfigDict, computed_field
from ..base import ValidationDetails


class DependencyIssue(BaseModel):
    """Single dependency issue."""
    model_config = ConfigDict(frozen=True)
    
    step_id: str
    missing_dependency: str
    issue_type: str  # "missing_step" | "missing_branch_target"


class CycleInfo(BaseModel):
    """Information about a detected cycle."""
    model_config = ConfigDict(frozen=True)
    
    cycle_path: List[str]
    
    @computed_field
    @property
    def cycle_length(self) -> int:
        return len(self.cycle_path)


class StructuralValidationDetails(ValidationDetails):
    """Structural-specific validation details."""
    dependency_issues: List[DependencyIssue] = Field(default_factory=list)
    cycles: List[CycleInfo] = Field(default_factory=list)
    orphaned_steps: Set[str] = Field(default_factory=set)
    
    @computed_field
    @property
    def has_cycles(self) -> bool:
        """Check if any cycles were detected."""
        return len(self.cycles) > 0
    
    def get_missing_steps(self) -> Set[str]:
        """Get all missing step references."""
        return {issue.missing_dependency for issue in self.dependency_issues 
                if issue.issue_type == "missing_step"}
    
    def get_missing_branch_targets(self) -> Set[str]:
        """Get all missing branch targets."""
        return {issue.missing_dependency for issue in self.dependency_issues 
                if issue.issue_type == "missing_branch_target"}
    
    @computed_field
    @property
    def total_issues(self) -> int:
        """Total number of structural issues."""
        return len(self.dependency_issues) + len(self.cycles) + len(self.orphaned_steps) 