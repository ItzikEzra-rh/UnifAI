from typing import List
from pydantic import BaseModel, ConfigDict, computed_field

from .base import ValidationReport, ValidationMessage


class ValidationResult(BaseModel):
    """Complete validation result from all validators."""
    model_config = ConfigDict(frozen=True)
    
    is_valid: bool
    connector_report: ValidationReport
    structural_report: ValidationReport
    semantic_report: ValidationReport
    
    @computed_field
    @property
    def all_messages(self) -> List[ValidationMessage]:
        messages = []
        for report in [self.connector_report, self.structural_report, self.semantic_report]:
            messages.extend(report.messages)
        return messages
    
    @computed_field
    @property
    def all_errors(self) -> List[ValidationMessage]:
        return [msg for msg in self.all_messages if msg.severity.value == "error"]
    
    @computed_field
    @property
    def all_warnings(self) -> List[ValidationMessage]:
        return [msg for msg in self.all_messages if msg.severity.value == "warning"]
