"""
Engine-level models for graph topology.

GraphDefinition is a fully serializable representation of a graph's
structure (nodes, edges, conditional routing).  It carries NO callables —
only string identifiers (uid, rid) that are resolved at execution time.

Used by engines that cannot carry live Python objects across process
boundaries (e.g., Temporal activities).
"""
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field


class NodeDef(BaseModel):
    """Identity of a single graph node."""
    uid: str
    rid: str  # Resource ID — resolved via SessionRegistry at execution time

    model_config = ConfigDict(frozen=True)


class ConditionalEdgeDef(BaseModel):
    """A conditional routing rule attached to a node."""
    condition_rid: str                  # Resource ID for the condition
    branches: Dict[str, str] = Field(   # outcome string → next node uid
        default_factory=dict,
    )

    model_config = ConfigDict(frozen=True)


class GraphDefinition(BaseModel):
    """
    Serializable graph topology.

    Contains only data (uids, rids, edges).  The workflow uses this
    for traversal decisions (which node next, which branch to take).
    Callables live separately in the GraphNodeActivities instance.
    """
    nodes: Dict[str, NodeDef] = Field(default_factory=dict)
    edges: Dict[str, List[str]] = Field(default_factory=dict)
    conditional_edges: Dict[str, ConditionalEdgeDef] = Field(default_factory=dict)
    entry: str = ""
    exit_node: str = ""   # 'exit' is a Python builtin

    model_config = ConfigDict(frozen=True)

    def get_predecessors(self) -> Dict[str, Set[str]]:
        """
        Compute reverse adjacency: { uid → {nodes that must finish first} }.

        Handles cycles: if node X has conditional branches to Y,
        and Y is also in X's after list (predecessors), the edge
        Y → X is a cycle-back edge, not a real prerequisite.
        These are removed so the node can start without deadlocking.

        Example:
          orchestrator after=["user_input", "jira_agent"]
          orchestrator branches={"jira_agent": "jira_agent", "done": "final"}

          jira_agent → orchestrator is a CYCLE-BACK edge (not prerequisite).
          user_input → orchestrator is a FORWARD edge (real prerequisite).
        """
        predecessors: Dict[str, Set[str]] = {uid: set() for uid in self.nodes}

        # Forward edges (from after relationships)
        for from_uid, to_uids in self.edges.items():
            for to_uid in to_uids:
                if to_uid in predecessors:
                    predecessors[to_uid].add(from_uid)

        # Conditional edge targets depend on the source
        for from_uid, cond in self.conditional_edges.items():
            for target_uid in cond.branches.values():
                if target_uid in predecessors:
                    predecessors[target_uid].add(from_uid)

        # Remove cycle-back edges:
        # If node X routes TO target Y via conditional branches,
        # and Y is also in X's predecessors (from after), then
        # Y → X is a back-edge. Remove it so X can start.
        for from_uid, cond in self.conditional_edges.items():
            for target_uid in cond.branches.values():
                predecessors[from_uid].discard(target_uid)

        return predecessors

    def get_successors(self, uid: str) -> List[str]:
        """Return unconditional successors of a node."""
        return list(self.edges.get(uid, []))
