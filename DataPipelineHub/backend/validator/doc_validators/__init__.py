from typing import Optional, Dict, Any, List, Tuple
from common.interfaces import DataSourceValidator, ValidationIssue


class DuplicateValidator(DataSourceValidator):
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
        DuplicateValidator(),
    ]


