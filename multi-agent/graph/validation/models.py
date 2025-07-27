from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from enum import Enum


class ValidationStatus(str, Enum):
    """Edge validation status for UI."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class PathValidation:
    """Validation result for a single execution path."""
    path_id: str
    steps: List[str]
    missing_channels: Dict[str, Set[str]]  # step_id -> missing channels
    impossible_channels: Dict[str, Set[str]]  # step_id -> impossible channels

    @property
    def is_valid(self) -> bool:
        return len(self.impossible_channels) == 0 and len(self.missing_channels) == 0


@dataclass(frozen=True)
class ValidationResult:
    """Complete graph validation result."""
    is_valid: bool
    path_validations: Dict[str, PathValidation]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DependencyMatrix:
    """Sparse matrix of channel dependencies."""
    producer_map: Dict[str, Set[Tuple[str, str]]]  # channel -> {(category, type_key)}
    consumer_map: Dict[str, Set[Tuple[str, str]]]  # channel -> {(category, type_key)}
    external_channels: Set[str]

    def can_produce(self, channel: str) -> bool:
        """Check if any element can produce this channel."""
        return channel in self.producer_map or channel in self.external_channels
