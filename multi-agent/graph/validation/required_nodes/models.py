from typing import Set
from pydantic import BaseModel, ConfigDict


class RequiredNodeIssue(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    node_type: str
    expected: str
    actual: str | None


class RequiredNodesDetails(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    required_node_issues: list[RequiredNodeIssue]
    missing_start_nodes: Set[str]
    missing_end_nodes: Set[str] 