from dataclasses import dataclass, field
from typing import Any, Dict


# @dataclass(frozen=True, slots=True) slots in python3.10+
@dataclass(frozen=True)
class StepContext:
    uid: str
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
