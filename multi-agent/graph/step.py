# graph/step.py

from typing import Any, Callable, List, Optional, Dict


class Step:
    """
    Represents one node in the abstract plan.

    Attributes:
        name: Unique identifier for this step.
        func: A callable(state: dict) -> dict implementing the step logic.
        after: List of step-names this step depends on.
        exit_condition: Optional name of a registered condition function
                        to decide whether to loop or branch.
        branches: Optional mapping from condition outcome to next step-name.
    """

    def __init__(
            self,
            name: str,
            func: Callable[[Dict[str, Any]], Dict[str, Any]],
            after: Optional[List[str]] = None,
            exit_condition: Optional[str] = None,
            branches: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.func = func
        self.after = after or []
        self.exit_condition = exit_condition
        self.branches = branches or {}

    def __repr__(self) -> str:
        return (
            f"Step(name={self.name!r}, after={self.after}, "
            f"exit_condition={self.exit_condition}, branches={self.branches})"
        )
