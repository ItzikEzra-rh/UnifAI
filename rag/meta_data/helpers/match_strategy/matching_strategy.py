from abc import ABC, abstractmethod
from typing import List, TypeVar

T = TypeVar('T')

class MatchingStrategy(ABC):
    """Abstract base class defining the interface for matching strategies."""
    
    @abstractmethod
    def matches(self, source_elements: List[T], target_elements: List[T]) -> bool:
        """
        Determines if elements match according to the strategy's criteria.
        
        Args:
            source_elements: List of elements to search for
            target_elements: List of elements to search in
            
        Returns:
            bool: True if the matching criteria is met, False otherwise
        """
        pass
    
class MatchingContext:
    """Context class that uses the matching strategies."""
    
    def __init__(self, strategy: MatchingStrategy):
        """
        Initialize the context with a specific strategy.
        
        Args:
            strategy: The matching strategy to use
        """
        self.strategy = strategy
    
    def set_strategy(self, strategy: MatchingStrategy) -> None:
        """
        Change the strategy at runtime.
        
        Args:
            strategy: The new matching strategy to use
        """
        self.strategy = strategy
    
    def check_match(self, source_elements: List[T], target_elements: List[T]) -> bool:
        """
        Apply the current strategy to check for matches.
        
        Args:
            source_elements: List of elements to search for
            target_elements: List of elements to search in
            
        Returns:
            bool: True if the matching criteria is met according to the current strategy
        """
        return self.strategy.matches(source_elements, target_elements)