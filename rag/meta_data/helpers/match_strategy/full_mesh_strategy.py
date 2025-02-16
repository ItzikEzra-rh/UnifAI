from .matching_strategy import MatchingStrategy
from typing import List, TypeVar

T = TypeVar('T')

class FullMeshStrategy(MatchingStrategy):
    """Strategy that requires all source elements to exist in target."""
    
    def matches(self, source_elements: List[T], target_elements: List[T]) -> bool:
        """
        Checks if all elements from source exist in target.
        
        Returns:
            bool: True if all elements match, False otherwise
        """
        return all(element in target_elements for element in source_elements)