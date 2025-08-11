"""
Core IEM Protocol Models
"""

from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime
from enum import Enum


class PacketKind(str, Enum):
    """IEM packet types."""
    REQUEST = "request"
    RESPONSE = "response" 
    EVENT = "event"





class ErrorCode(str, Enum):
    """Standard IEM error codes."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    ADJACENCY_ERROR = "ADJACENCY_ERROR"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"


class StandardActions(str, Enum):
    """Common action names for consistency."""
    # Processing actions
    PROCESS_USER_INPUT = "process_user_input"
    ANALYZE_TEXT = "analyze_text"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"
    EXTRACT_ENTITIES = "extract_entities"
    
    # Data actions
    SEARCH = "search"
    RETRIEVE = "retrieve"
    EMBED = "embed"
    STORE = "store"
    
    # Workflow actions
    VALIDATE = "validate"
    TRANSFORM = "transform"
    MERGE = "merge"
    ROUTE = "route"
    
    # System actions
    HEALTH_CHECK = "health_check"
    GET_STATUS = "get_status"
    GET_CAPABILITIES = "get_capabilities"


class StandardEvents(str, Enum):
    """Common event types for consistency."""
    # Processing events
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETE = "processing_complete"
    PROCESSING_FAILED = "processing_failed"
    
    # Task events
    TASK_COMPLETE = "task_complete"
    
    # Task events
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_FAILED = "workflow_failed"
    
    # Consolidation events
    CONSOLIDATION_COMPLETE = "consolidation_complete"
    CONSOLIDATION_FAILED = "consolidation_failed"
    
    # System events
    NODE_READY = "node_ready"
    NODE_SHUTDOWN = "node_shutdown"
    HEALTH_STATUS = "health_status"


class ElementAddress(BaseModel):
    """Address for an element in the graph."""
    uid: str
    type_key: Optional[str] = None
    name: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.name or self.type_key or 'unknown'}({self.uid})"
    
    def __hash__(self) -> int:
        return hash(self.uid)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, ElementAddress):
            return self.uid == other.uid
        return False


class IEMError(BaseModel):
    """Structured error information for IEM responses."""
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def validation_error(cls, message: str, **details) -> 'IEMError':
        """Create a validation error."""
        return cls(code=ErrorCode.VALIDATION_ERROR, message=message, details=details)
    
    @classmethod
    def permission_denied(cls, message: str, **details) -> 'IEMError':
        """Create a permission denied error."""
        return cls(code=ErrorCode.PERMISSION_DENIED, message=message, details=details)
    
    @classmethod
    def timeout_error(cls, message: str, **details) -> 'IEMError':
        """Create a timeout error."""
        return cls(code=ErrorCode.TIMEOUT_ERROR, message=message, details=details)
    
    @classmethod
    def not_found_error(cls, message: str, **details) -> 'IEMError':
        """Create a not found error."""
        return cls(code=ErrorCode.NOT_FOUND, message=message, details=details)
    
    @classmethod
    def internal_error(cls, message: str, **details) -> 'IEMError':
        """Create an internal error."""
        return cls(code=ErrorCode.INTERNAL_ERROR, message=message, details=details)
    
    @classmethod
    def adjacency_error(cls, message: str, **details) -> 'IEMError':
        """Create an adjacency error."""
        return cls(code=ErrorCode.ADJACENCY_ERROR, message=message, details=details)
    
    @classmethod
    def protocol_error(cls, message: str, **details) -> 'IEMError':
        """Create a protocol error."""
        return cls(code=ErrorCode.PROTOCOL_ERROR, message=message, details=details)
