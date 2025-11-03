from typing import Optional, Dict, Any, List, Tuple
from common.interfaces import DataSourceValidator, ValidationIssue
from .doc_validators import build_doc_validators


class Validator:
    """Runs a list of validators with optional fail-fast behavior."""

    def __init__(self, validators: List[DataSourceValidator], fail_fast: bool = True) -> None:
        self.validators = validators
        self.fail_fast = fail_fast

    def validate(self, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[ValidationIssue]]:
        errors: List[str] = []

        for validator in self.validators:
            is_valid, issue = validator.validate(args, context)
            if not is_valid:
                if self.fail_fast:
                    return False, issue
                # Accumulate human-friendly messages
                if issue:
                    errors.append(f"{issue.get('validator_name')}: {issue.get('message')}")

        if errors:
            return False, {"issue_key": "ValidationError", "message": "; ".join(errors), "validator_name": "Validator"}
        return True, None
