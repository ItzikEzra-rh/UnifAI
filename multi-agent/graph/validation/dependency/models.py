from typing import Literal
from pydantic import BaseModel, ConfigDict


class DependencyIssue(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    step_id: str
    missing_dependency: str
    issue_type: Literal["missing_step", "missing_branch_target"] 