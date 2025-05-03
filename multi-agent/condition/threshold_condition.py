from typing import Any, Dict
import operator
from .base_condition import BaseCondition


class ThresholdCondition(BaseCondition):
    """
    Returns True or False depending on whether state[input_key]
    compares against threshold with the given operator.
    """

    OPERATORS = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, input_key: str, threshold: float, operator: str = ">"):
        if operator not in self.OPERATORS:
            raise ValueError(f"Unsupported operator: {operator}")
        self.input_key = input_key
        self.threshold = threshold
        self.operator_fn = self.OPERATORS[operator]

    def __call__(self, state: Dict[str, Any]) -> bool:
        """
        Fetches `value = state[self.input_key]`, then returns
        operator_fn(value, threshold).
        """
        value = state.get(self.input_key)
        return self.operator_fn(value, self.threshold)

    def __repr__(self) -> str:
        return (
            f"<ThresholdCondition: {self.input_key} {self._operator_symbol()} {self.threshold}>"
        )

    def _operator_symbol(self) -> str:
        # Reverse lookup from function to symbol
        for symbol, func in self.OPERATORS.items():
            if func == self.operator_fn:
                return symbol
        return "<?>"
