from dataclasses import dataclass, field
from blueprints.models.blueprint import StepMeta


# @dataclass(frozen=True, slots=True) slots in python3.10+
@dataclass(frozen=True)
class StepContext:
    uid: str
    metadata: StepMeta = field(default_factory=StepMeta())
