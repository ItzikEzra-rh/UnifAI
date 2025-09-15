from typing import Optional, Dict, Any, List, Tuple
from common.interfaces import DataSourceValidator, ValidationIssue


class _DuplicateValidator(DataSourceValidator):
    name = "DuplicateValidator"
    error_message = "This file appears to be a duplicate from an existing file and was not added. File: {source_name}"
    error_message_key = "File duplicated error"
    
    async def validate(self, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[ValidationIssue]]:
        if not context:
            return True, None

        duplicate_checker = context.get("duplicate_checker") if isinstance(context, dict) else None
        if duplicate_checker and hasattr(duplicate_checker, "is_duplicate"):
            try:
                if duplicate_checker.is_duplicate(args):
                    # User-facing, clear message consumed by UI toasts
                    return False, self.build_issue(
                        self.error_message.format(source_name=args.get("source_name"))
                    )
            except Exception:
                return True, None

        return True, None


def build_doc_validators() -> List[DataSourceValidator]:
    """Return the default list of validators to apply to a single doc.

    Keep this minimal and composable; callers can extend/replace as needed.
    """
    return [
        _DuplicateValidator(),
    ]


class ValidatorRunner:
    """Runs a list of validators with optional fail-fast behavior."""

    def __init__(self, validators: List[DataSourceValidator], fail_fast: bool = True) -> None:
        self.validators = validators
        self.fail_fast = fail_fast

    async def validate(self, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[ValidationIssue]]:
        errors: List[str] = []

        for validator in self.validators:
            is_valid, issue = await validator.validate(args, context)
            if not is_valid:
                if self.fail_fast:
                    return False, issue
                # Accumulate human-friendly messages
                if issue:
                    errors.append(f"{issue.get('validator_name')}: {issue.get('message')}")

        if errors:
            return False, {"issue_key": "ValidationError", "message": "; ".join(errors), "validator_name": "ValidatorRunner"}
        return True, None
