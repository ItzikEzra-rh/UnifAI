from typing import List, Set, Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field
from ..base import ValidationDetails


class RequiredNodeIssue(BaseModel):
    """Issue with required nodes."""
    model_config = ConfigDict(frozen=True)
    
    node_type: str  # "start" | "end"
    expected: str
    actual: Optional[str] = None


class RuleViolation(BaseModel):
    """Business rule violation."""
    model_config = ConfigDict(frozen=True)
    
    rule_name: str
    description: str
    affected_steps: List[str] = Field(default_factory=list)


class SemanticValidationDetails(ValidationDetails):
    """Semantic-specific validation details."""
    required_node_issues: List[RequiredNodeIssue] = Field(default_factory=list)
    missing_start_nodes: Set[str] = Field(default_factory=set)
    missing_end_nodes: Set[str] = Field(default_factory=set)
    rule_violations: List[RuleViolation] = Field(default_factory=list)
    
    def has_start_node_issues(self) -> bool:
        """Check if there are start node issues."""
        return len(self.missing_start_nodes) > 0
    
    def has_end_node_issues(self) -> bool:
        """Check if there are end node issues."""
        return len(self.missing_end_nodes) > 0
    
    def has_rule_violations(self) -> bool:
        """Check if there are rule violations."""
        return len(self.rule_violations) > 0
    
    @computed_field
    @property
    def total_issues(self) -> int:
        """Total number of semantic issues."""
        return len(self.required_node_issues) + len(self.rule_violations) 