"""
Standardized Payloads for IEM Protocol

Defines Pydantic models for common task lifecycle and workflow payloads
to be used with StandardEvents and StandardActions.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime


class TaskAssignedPayload(BaseModel):
    """Payload for StandardEvents.TASK_ASSIGNED events."""
    task_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    parent_task_id: Optional[str] = None
    priority: Optional[int] = None
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskStartedPayload(BaseModel):
    """Payload for StandardEvents.TASK_STARTED events."""
    task_id: str
    started_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    estimated_duration: Optional[int] = None  # seconds
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskProgressPayload(BaseModel):
    """Payload for task progress updates."""
    task_id: str
    step: Optional[int] = None
    total_steps: Optional[int] = None
    message: Optional[str] = None
    percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskResultPayload(BaseModel):
    """Payload for StandardEvents.TASK_COMPLETED events."""
    task_id: str
    output: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    duration: Optional[int] = None  # seconds


class TaskFailedPayload(BaseModel):
    """Payload for StandardEvents.TASK_FAILED events."""
    task_id: str
    error_code: Optional[str] = None
    error_message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: Optional[int] = None
    max_retries: Optional[int] = None


class TaskCancelledPayload(BaseModel):
    """Payload for StandardEvents.TASK_CANCELLED events."""
    task_id: str
    reason: Optional[str] = None
    cancelled_at: datetime = Field(default_factory=datetime.utcnow)
    cancelled_by: Optional[str] = None


class ProcessingStartedPayload(BaseModel):
    """Payload for StandardEvents.PROCESSING_STARTED events."""
    user_query: str
    source_node: Dict[str, str] = Field(default_factory=dict)
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessingCompletePayload(BaseModel):
    """Payload for StandardEvents.PROCESSING_COMPLETE events."""
    result: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    thread_id: Optional[str] = None
    duration: Optional[int] = None  # seconds
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStartedPayload(BaseModel):
    """Payload for StandardEvents.WORKFLOW_STARTED events."""
    workflow_id: str
    workflow_type: Optional[str] = None
    input_params: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowCompletePayload(BaseModel):
    """Payload for StandardEvents.WORKFLOW_COMPLETE events."""
    workflow_id: str
    output: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    total_tasks: Optional[int] = None
    successful_tasks: Optional[int] = None
    failed_tasks: Optional[int] = None


class NodeReadyPayload(BaseModel):
    """Payload for StandardEvents.NODE_READY events."""
    node_id: str
    node_type: str
    capabilities: List[str] = Field(default_factory=list)
    ready_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthStatusPayload(BaseModel):
    """Payload for StandardEvents.HEALTH_STATUS events."""
    node_id: str
    status: str  # "healthy", "degraded", "unhealthy"
    checks: Dict[str, bool] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Common request payloads for StandardActions

class ProcessUserInputPayload(BaseModel):
    """Payload for StandardActions.PROCESS_USER_INPUT requests."""
    user_input: str
    context: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class AnalyzeTextPayload(BaseModel):
    """Payload for StandardActions.ANALYZE_TEXT requests."""
    text: str
    analysis_type: Optional[str] = None  # "sentiment", "entities", "summary", etc.
    options: Dict[str, Any] = Field(default_factory=dict)


class SearchPayload(BaseModel):
    """Payload for StandardActions.SEARCH requests."""
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: Optional[int] = None
    offset: Optional[int] = None


class ValidatePayload(BaseModel):
    """Payload for StandardActions.VALIDATE requests."""
    data: Dict[str, Any]
    validation_schema: Optional[Dict[str, Any]] = None
    rules: List[str] = Field(default_factory=list)


class TransformPayload(BaseModel):
    """Payload for StandardActions.TRANSFORM requests."""
    data: Any
    transform_type: str
    params: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckPayload(BaseModel):
    """Payload for StandardActions.HEALTH_CHECK requests."""
    deep: bool = False
    components: List[str] = Field(default_factory=list)


class GetStatusPayload(BaseModel):
    """Payload for StandardActions.GET_STATUS requests."""
    include_metrics: bool = False
    include_history: bool = False
    time_range: Optional[int] = None  # seconds


class TaskPayload(BaseModel):
    """Universal task payload for all agent communication."""
    result: str
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
