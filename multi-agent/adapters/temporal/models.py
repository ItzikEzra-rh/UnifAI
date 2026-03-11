"""
Temporal DTO models.

Serializable parameter objects for workflows and activities.
These are the transport-layer data contracts for Temporal SDK.

Shared by both inbound (worker/activities/workflows) and outbound
(executor/submitter) Temporal adapters.
"""
from typing import Any, Dict
from pydantic import BaseModel, Field


# ── Workflow params ──────────────────────────────────────────────────

class GraphExecutionParams(BaseModel):
    """Input to GraphTraversalWorkflow."""
    state: Dict[str, Any] = Field(default_factory=dict)
    graph_definition: Dict[str, Any] = Field(default_factory=dict)
    session_id: str = ""


class SessionWorkflowParams(BaseModel):
    """Input to SessionWorkflow (parent workflow).

    Carries the session execution context (for lifecycle activities)
    and the nested graph execution params (for the child
    GraphTraversalWorkflow).  The workflow owns the full lifecycle:
    begin → execute → complete/fail.

    Inputs are already staged into the SessionRecord before the
    workflow starts — no raw inputs are passed here.
    """
    run_id: str
    scope: str = "public"
    logged_in_user: str = ""
    graph_execution_params: Dict[str, Any] = Field(default_factory=dict)


# ── Activity params ──────────────────────────────────────────────────

class ExecuteNodeParams(BaseModel):
    """Input to the execute_graph_node activity."""
    node_uid: str
    node_blueprint: Dict[str, Any] = Field(default_factory=dict)
    step_context: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    session_id: str = ""


class EvaluateConditionParams(BaseModel):
    """Input to the evaluate_condition activity."""
    condition_rid: str
    condition_blueprint: Dict[str, Any] = Field(default_factory=dict)
    step_context: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)


class BeginSessionParams(BaseModel):
    """Input to the begin_session activity.

    Inputs are already staged — this only transitions QUEUED → RUNNING.
    """
    run_id: str
    scope: str = "public"
    logged_in_user: str = ""


class CompleteSessionParams(BaseModel):
    """Input to the complete_session activity."""
    run_id: str
    final_state: Dict[str, Any] = Field(default_factory=dict)


class FailSessionParams(BaseModel):
    """Input to the fail_session activity."""
    run_id: str
    error_message: str = ""
