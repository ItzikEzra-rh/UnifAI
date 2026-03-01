"""
Data models for the Temporal graph engine.

Serializable parameter objects for workflows and activities.
"""
from typing import Any, Dict
from pydantic import BaseModel, Field


class GraphExecutionParams(BaseModel):
    """Input to GraphTraversalWorkflow."""
    state: Dict[str, Any] = Field(default_factory=dict)
    graph_definition: Dict[str, Any] = Field(default_factory=dict)


class ExecuteNodeParams(BaseModel):
    """Input to the execute_graph_node activity."""
    node_uid: str
    state: Dict[str, Any] = Field(default_factory=dict)


class EvaluateConditionParams(BaseModel):
    """Input to the evaluate_condition activity."""
    condition_rid: str
    state: Dict[str, Any] = Field(default_factory=dict)
