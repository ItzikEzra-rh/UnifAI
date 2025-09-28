"""
Cycle detection for GraphPlan objects.

Clean OOP design for cycle analysis.
"""

from typing import Dict, Set, List, Tuple
from collections import deque
from .graph_builder import EdgeType, GraphAnalyzer


class CycleInfo:
    """Information about a detected cycle."""
    
    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
    
    @property
    def cycle_length(self) -> int:
        """Length of the cycle path."""
        return len(self.cycle_path)


class CycleDetector:
    """
    Cycle detector that works with GraphPlan objects.
    
    Clean interface for cycle detection operations.
    """
    
    def __init__(self, plan: 'GraphPlan'):
        self.analyzer = GraphAnalyzer(plan)
    
    def detect_all_cycles(self) -> List[CycleInfo]:
        """Detect all cycles in the graph."""
        cycles = []
        visited = set()
        rec_stack = set()

        for node in self.analyzer.adjacency:
            if node not in visited:
                found_cycles = self._dfs_cycle_detection(
                    node, visited, rec_stack, []
                )
                cycles.extend(found_cycles)

        return cycles
    
    def _dfs_cycle_detection(
        self,
        node: str, 
        visited: Set[str], 
        rec_stack: Set[str],
        path: List[str]
    ) -> List[CycleInfo]:
        """DFS-based cycle detection."""
        visited.add(node)
        rec_stack.add(node)
        current_path = path + [node]
        cycles = []

        for neighbor in self.analyzer.adjacency.get(node, set()):
            if neighbor not in visited:
                cycles.extend(self._dfs_cycle_detection(
                    neighbor, visited, rec_stack, current_path
                ))
            elif neighbor in rec_stack:
                # Found cycle - extract cycle path
                try:
                    cycle_start_idx = current_path.index(neighbor)
                    cycle_path = current_path[cycle_start_idx:] + [neighbor]
                    cycles.append(CycleInfo(cycle_path=cycle_path))
                except ValueError:
                    # Handle edge case where neighbor not in current path
                    cycle_path = current_path + [neighbor]
                    cycles.append(CycleInfo(cycle_path=cycle_path))

        rec_stack.remove(node)
        return cycles
    
    def is_dangerous_cycle(self, cycle: CycleInfo) -> bool:
        """
        Determine if a cycle is dangerous (inescapable or unconditional).
        """
        # Normalize cycle path (last element duplicates the first)
        path = cycle.cycle_path
        if len(path) > 1 and path[0] == path[-1]:
            path = path[:-1]

        cycle_nodes = set(path)

        # Rule 1: unconditional edge inside cycle?
        for u, v in zip(path, path[1:] + [path[0]]):
            if self.analyzer.edge_types.get((u, v)) == EdgeType.AFTER:
                return True  # unconditional loop -> dangerous

        # Rule 2: all edges are branch; check for exit path
        return not self._cycle_has_exit(cycle_nodes)
    
    def _cycle_has_exit(self, cycle_nodes: Set[str]) -> bool:
        """Check if a cycle has an exit path to any terminal node."""
        terminal_nodes = self.analyzer.get_terminal_nodes()
        queue = deque(cycle_nodes)
        visited = set(cycle_nodes)

        while queue:
            node = queue.popleft()
            for neighbor in self.analyzer.adjacency.get(node, set()):
                if neighbor in visited:
                    continue
                if neighbor in terminal_nodes:
                    return True  # Found an exit path
                visited.add(neighbor)
                queue.append(neighbor)

        return False  # No exits found
