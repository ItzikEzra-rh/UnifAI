from .matching_strategy import MatchingStrategy
from typing import List, TypeVar

T = TypeVar('T')

class SingleMatchStrategy(MatchingStrategy):
    """Strategy that requires at least one element to match (equivalent to any())."""
    
    def matches(self, source_elements: List[T], target_elements: List[T]) -> bool:
        """
        Checks if at least one element from source exists in target.
        
        Returns:
            bool: True if at least one element matches, False otherwise
        """
        return any(element in target_elements for element in source_elements)
