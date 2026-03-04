"""
Temporal DTO models.

Serializable parameter objects for workflows and activities.
These are the transport-layer data contracts for Temporal SDK.
"""
from typing import Any, Dict
from pydantic import BaseModel, Field


# ── Workflow params ──────────────────────────────────────────────────

class GraphExecutionParams(BaseModel):
    """Input to GraphTraversalWorkflow."""
    state: Dict[str, Any] = Field(default_factory=dict)
    graph_definition: Dict[str, Any] = Field(default_factory=dict)


class SessionWorkflowParams(BaseModel):
    """Input to SessionWorkflow (parent workflow).

    Carries both the session run_id (for lifecycle activities) and the
    nested graph execution params (for the child GraphTraversalWorkflow).
    """
    run_id: str
    graph_execution_params: Dict[str, Any] = Field(default_factory=dict)


# ── Activity params ──────────────────────────────────────────────────

class ExecuteNodeParams(BaseModel):
    """Input to the execute_graph_node activity."""
    node_uid: str
    node_blueprint: Dict[str, Any] = Field(default_factory=dict)
    step_context: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)


class EvaluateConditionParams(BaseModel):
    """Input to the evaluate_condition activity."""
    condition_rid: str
    condition_blueprint: Dict[str, Any] = Field(default_factory=dict)
    step_context: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)


class CompleteSessionParams(BaseModel):
    """Input to the complete_session activity."""
    run_id: str
    final_state: Dict[str, Any] = Field(default_factory=dict)


class FailSessionParams(BaseModel):
    """Input to the fail_session activity."""
    run_id: str
    error_message: str = ""
