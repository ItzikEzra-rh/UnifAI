from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict
from graph.graph_plan import GraphPlan


class MessageSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class MessageCode(str, Enum):
    # Connector validation codes
    IMPOSSIBLE_CHANNELS = "IMPOSSIBLE_CHANNELS"
    MISSING_CHANNELS = "MISSING_CHANNELS"
    
    # Structural validation codes
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
    MISSING_BRANCH_TARGET = "MISSING_BRANCH_TARGET"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    ORPHANED_STEP = "ORPHANED_STEP"
    
    # Semantic validation codes
    MISSING_START_NODE = "MISSING_START_NODE"
    MISSING_END_NODE = "MISSING_END_NODE"
    MISSING_REQUIRED_NODE = "MISSING_REQUIRED_NODE"


class ValidationMessage(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    text: str
    severity: MessageSeverity
    code: Optional[MessageCode] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class ValidationDetails(BaseModel):
    model_config = ConfigDict(frozen=True)


class ValidationReport(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    validator_name: str
    is_valid: bool
    messages: List[ValidationMessage] = Field(default_factory=list)
    details: Optional[Any] = None
    
    @property
    def errors(self) -> List[ValidationMessage]:
        return [msg for msg in self.messages if msg.severity == MessageSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationMessage]:
        return [msg for msg in self.messages if msg.severity == MessageSeverity.WARNING]


class Validator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def validate(self, plan: GraphPlan) -> ValidationReport:
        pass


class SuggestsFixes(Protocol):
    def suggest_fixes(self, plan: GraphPlan) -> List:
        ... 