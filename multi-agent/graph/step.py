from typing import Any, Dict, List, Optional


class Step:
    """
    Represents a single node execution within the plan.

    Attributes:
        name:            Unique identifier for this step.
        func:            A callable taking `state: dict` and returning `state: dict`.
        after:           List of step-names that must complete before this one.
        exit_condition:  Optional name of a condition function (in ElementRegistry)
                         that controls whether to loop or branch.
        branches:        Optional mapping from condition outcome to next step-name.
    """

    def __init__(
            self,
            name: str,
            func: Any,
            after: Optional[List[str]] = None,
            exit_condition: Optional[str] = None,
            branches: Optional[Dict[str, str]] = None
    ) -> None:
        self.name = name
        self.func = func
        self.after = after or []
        self.exit_condition = exit_condition
        self.branches = branches or {}

    def __repr__(self) -> str:
        return (
            f"<Step name={self.name!r} "
            f"after={self.after} "
            f"exit_condition={self.exit_condition!r} "
            f"branches={self.branches}>"
        )
