from dataclasses import dataclass, field
from typing import Dict, Set

from blueprints.models.blueprint import StepMeta


# ─────────────────────────────────────────────────────────────────────────────
#  Helper value object: information about a *target* node in a branch
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BranchNodeInfo:
    """Read‐only snapshot describing a node pointed to by a branch."""

    uid: str
    type_key: str
    metadata: StepMeta
    reads: Set[str]
    writes: Set[str]


# @dataclass(frozen=True, slots=True) slots once we migrate to Python ≥3.10
@dataclass(frozen=True)
class StepContext:
    """Immutable context object injected into nodes / conditions at runtime."""

    # Identity & author metadata
    uid: str
    metadata: StepMeta = field(default_factory=StepMeta)

    # Branching structure (outcome → next uid)
    branches: Dict[str, str] = field(default_factory=dict)

    # Rich info about the *target* nodes (outcome → BranchNodeInfo)
    branch_nodes: Dict[str, BranchNodeInfo] = field(default_factory=dict)
