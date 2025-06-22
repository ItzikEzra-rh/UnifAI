from typing import Any, Dict, List, Optional
from blueprints.models.blueprint import StepMeta


class Step:
    """
    Represents a single node execution within the plan.

    Attributes:
        uid:            Unique identifier for this step.
        func:            A callable taking `state: dict` and returning `state: dict`.
        after:           List of step-uids that must complete before this one.
        exit_condition:  Optional uid of a condition function (in ElementRegistry)
                         that controls whether to loop or branch.
        branches:        Optional mapping from condition outcome to next step-uid.
        meta:           Optional metadata for this step instance.
    """

    def __init__(
            self,
            uid: str,
            func: Any,
            after: Optional[List[str]] = None,
            exit_condition: Any = None,
            branches: Optional[Dict[str, str]] = None,
            meta: Optional[StepMeta] = StepMeta()
    ) -> None:
        self.uid = uid
        self.func = func
        self.after = after or []
        self.exit_condition = exit_condition
        self.branches = branches or {}
        self.meta = meta or StepMeta()

    def __repr__(self) -> str:
        return (
            f"<Step uid={self.uid!r} "
            f"after={self.after} "
            f"exit_condition={self.exit_condition!r} "
            f"branches={self.branches}>"
            f"meta={self.meta} "
        )
