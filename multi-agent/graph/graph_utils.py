# graph/graph_utils.py

from typing import List, Dict, Set
from graph.step import Step


def detect_cycles(steps: List[Step]) -> bool:
    """
    Simple cycle detection in a directed graph of Steps based on 'after' edges.
    Returns True if a cycle exists.

    Uses DFS with recursion stack to detect back-edges.
    """
    graph: Dict[str, List[str]] = {s.name: s.after for s in steps}
    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def visit(node: str) -> bool:
        if node in rec_stack:
            return True  # back-edge found
        if node in visited:
            return False
        visited.add(node)
        rec_stack.add(node)
        for dep in graph.get(node, []):
            if visit(dep):
                return True
        rec_stack.remove(node)
        return False

    return any(visit(s.name) for s in steps)
