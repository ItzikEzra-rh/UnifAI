from .matching_strategy import MatchingStrategy
from typing import List, TypeVar

T = TypeVar('T')

class HalfMeshStrategy(MatchingStrategy):
    """Strategy that requires at least half of the source elements to exist in target."""
    
    def matches(self, source_elements: List[T], target_elements: List[T]) -> bool:
        """
        Checks if at least half of the elements from source exist in target.
        
        Returns:
            bool: True if half or more elements match, False otherwise
        """
        if not source_elements:
            return True
            
        matches = sum(1 for element in source_elements if element in target_elements)
        return matches >= len(source_elements) / 2