"""
Topology models for graph analysis.

Clean, extensible Pydantic models for topology information using composition.
"""

from typing import Dict, Optional, List
from pydantic import BaseModel, Field, computed_field


class CycleInfo(BaseModel):
    """Information about a detected cycle in the graph."""
    
    cycle_path: List[str] = Field(..., description="Ordered list of node UIDs forming the cycle")
    
    @computed_field
    @property
    def cycle_length(self) -> int:
        """Length of the cycle path."""
        return len(self.cycle_path)
    
    class Config:
        frozen = True


class FinalizerDistance(BaseModel):
    """Distance from a node to a finalizer."""
    node_uid: str = Field(..., description="UID of the adjacent node")
    distance: int = Field(..., ge=1, description="Number of hops to nearest finalizer")
    
    class Config:
        frozen = True


class FinalizerPathInfo(BaseModel):
    """
    Information about paths from adjacent nodes to finalizer nodes.
    
    A finalizer is a node that writes to Channel.OUTPUT.
    This model contains distance information for adjacent nodes that can
    reach finalizers without creating cycles.
    """
    distances: Dict[str, int] = Field(
        default_factory=dict,
        description="Map of adjacent node UID to distance to nearest finalizer (OUTPUT channel writer). "
                   "Only includes adjacent nodes that have a non-cyclic path to a finalizer."
    )
    
    class Config:
        frozen = True
        extra = "forbid"
    
    def get_nearest_finalizer_node(self) -> Optional[str]:
        """
        Get the UID of the adjacent node with the shortest path to a finalizer.
        
        Returns:
            UID of the adjacent node with shortest path to finalizer, or None if no paths exist
        """
        if not self.distances:
            return None
        return min(self.distances.items(), key=lambda x: x[1])[0]
    
    def get_shortest_distance(self) -> Optional[int]:
        """
        Get the shortest distance to a finalizer through any adjacent node.
        
        Returns:
            Shortest distance to finalizer, or None if no paths exist
        """
        if not self.distances:
            return None
        return min(self.distances.values())
    
    def has_finalizer_paths(self) -> bool:
        """Check if any adjacent node can reach a finalizer without cycles."""
        return bool(self.distances)
    
    def get_reachable_nodes(self) -> List[str]:
        """Get list of adjacent node UIDs that can reach a finalizer."""
        return list(self.distances.keys())
    
    def get_distance(self, adjacent_node_uid: str) -> Optional[int]:
        """
        Get distance from specific adjacent node to nearest finalizer.
        
        Args:
            adjacent_node_uid: UID of the adjacent node to check
            
        Returns:
            Distance to finalizer through this node, or None if no path exists
        """
        return self.distances.get(adjacent_node_uid)


class StepTopology(BaseModel):
    """
    Generic topology information for a specific step in the graph.
    
    Uses composition to contain different types of topology information.
    This design allows for easy extension with new topology aspects
    without breaking existing code.
    
    Immutable after creation, provides topology insights without
    coupling to specific implementations.
    """
    
    # Finalizer path information
    finalizer_paths: Optional[FinalizerPathInfo] = Field(
        default=None,
        description="Information about paths to finalizer nodes (nodes writing to Channel.OUTPUT)"
    )
    
    # Future topology aspects can be added here:
    # cycle_info: Optional[CycleInfo] = None
    # centrality: Optional[CentralityInfo] = None  
    # clustering: Optional[ClusterInfo] = None
    # critical_path: Optional[CriticalPathInfo] = None
    
    class Config:
        frozen = True
        extra = "forbid"  # Strict schema to catch typos
    
    # Convenience methods that delegate to finalizer_paths
    def has_finalizer_path(self) -> bool:
        """Check if any adjacent node can reach a finalizer without cycles."""
        return self.finalizer_paths is not None and self.finalizer_paths.has_finalizer_paths()
    
    def get_nearest_finalizer_node(self) -> Optional[str]:
        """Get the UID of the adjacent node with shortest path to finalizer."""
        if self.finalizer_paths is None:
            return None
        return self.finalizer_paths.get_nearest_finalizer_node()
    
    def get_shortest_finalizer_distance(self) -> Optional[int]:
        """Get the shortest distance to a finalizer through any adjacent node."""
        if self.finalizer_paths is None:
            return None
        return self.finalizer_paths.get_shortest_distance()
    
    def get_finalizer_reachable_nodes(self) -> List[str]:
        """Get list of adjacent node UIDs that can reach a finalizer."""
        if self.finalizer_paths is None:
            return []
        return self.finalizer_paths.get_reachable_nodes()
    
    def get_distance_to_finalizer(self, adjacent_node_uid: str) -> Optional[int]:
        """Get distance from specific adjacent node to nearest finalizer."""
        if self.finalizer_paths is None:
            return None
        return self.finalizer_paths.get_distance(adjacent_node_uid)


# No backward compatibility - use StepTopology with FinalizerPathInfo composition