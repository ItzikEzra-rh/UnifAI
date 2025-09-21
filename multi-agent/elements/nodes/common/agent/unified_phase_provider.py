"""
Unified phase provider following SOLID principles.

This module provides a single, cohesive interface for all phase-related concerns,
replacing multiple separate providers with a clean, unified design.
"""

from typing import Protocol, List, Dict, Optional
from abc import ABC, abstractmethod
from elements.tools.common.base_tool import BaseTool
from .constants import ExecutionPhase
from .phase_protocols import PhaseState
from .phase_guidance import PhaseGuidanceProvider

# Forward declaration for AgentObservation
from typing import TYPE_CHECKING
from ..primitives import AgentObservation


class PhaseProvider(Protocol):
    """
    Unified protocol for all phase-related concerns.
    
    This single interface replaces multiple separate providers:
    - PhaseContextProvider
    - PhaseToolProvider  
    - PhaseTransitionPolicy
    - Phase guidance
    
    Benefits:
    - Single dependency for strategies (Interface Segregation)
    - Cohesive phase management (Single Responsibility)
    - Easy to implement and test
    - Extensible for different phase systems
    """
    
    def get_phase_context(self) -> PhaseState:
        """Get current phase context for decision making."""
        ...
    
    def get_tools_for_phase(self, phase: ExecutionPhase) -> List[BaseTool]:
        """Get tools appropriate for the given phase."""
        ...
    
    def get_phase_guidance(self, phase: ExecutionPhase) -> str:
        """Get concise guidance for the given phase."""
        ...
    
    def decide_next_phase(
        self,
        *,
        current_phase: ExecutionPhase,
        phase_state: PhaseState,
        observations: List['AgentObservation']
    ) -> ExecutionPhase:
        """Decide the next execution phase based on current state."""
        ...


class BasePhaseProvider(ABC):
    """
    Abstract base class for phase providers.
    
    Provides common functionality while allowing customization of specific concerns.
    Follows Template Method pattern for extensibility.
    """
    
    def __init__(self, tools: List[BaseTool]):
        """
        Initialize with available tools.
        
        Args:
            tools: All available tools for phase categorization
        """
        self._tools = tools
    
    def get_phase_guidance(self, phase: ExecutionPhase) -> str:
        """
        Get concise guidance for the given phase.
        
        Uses PhaseGuidanceProvider for consistency across implementations.
        """
        return PhaseGuidanceProvider.get_guidance(phase)
    
    @abstractmethod
    def get_phase_context(self) -> PhaseState:
        """Get current phase context - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_tools_for_phase(self, phase: ExecutionPhase) -> List[BaseTool]:
        """Get tools for phase - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def decide_next_phase(
        self,
        *,
        current_phase: ExecutionPhase,
        phase_state: PhaseState,
        observations: List['AgentObservation']
    ) -> ExecutionPhase:
        """Decide next phase - must be implemented by subclasses."""
        pass


class DefaultPhaseProvider(BasePhaseProvider):
    """
    Default implementation of PhaseProvider for simple use cases.
    
    Provides basic phase management without external dependencies.
    Suitable for testing or simple scenarios.
    """
    
    def __init__(self, tools: List[BaseTool], node_uid: str = "default"):
        """
        Initialize default phase provider.
        
        Args:
            tools: Available tools
            node_uid: Node identifier for context
        """
        super().__init__(tools)
        self._node_uid = node_uid
    
    def get_phase_context(self) -> PhaseState:
        """Get minimal phase context."""
        from .phase_protocols import create_phase_state
        return create_phase_state(node_uid=self._node_uid)
    
    def get_tools_for_phase(self, phase: ExecutionPhase) -> List[BaseTool]:
        """Return all tools for all phases (no filtering)."""
        return self._tools.copy()
    
    def decide_next_phase(
        self,
        *,
        current_phase: ExecutionPhase,
        phase_state: PhaseState,
        observations: List['AgentObservation']
    ) -> ExecutionPhase:
        """Simple phase progression: PLANNING -> EXECUTION -> SYNTHESIS."""
        if current_phase == ExecutionPhase.PLANNING:
            return ExecutionPhase.EXECUTION
        elif current_phase == ExecutionPhase.EXECUTION:
            return ExecutionPhase.SYNTHESIS
        else:
            return ExecutionPhase.SYNTHESIS  # Stay in synthesis


# =============================================================================
# PHASE PROVIDER FACTORY
# =============================================================================

class PhaseProviderFactory:
    """
    Factory for creating appropriate phase providers.
    
    Follows Factory pattern to encapsulate provider creation logic.
    Makes it easy to switch between different phase provider implementations.
    """
    
    @staticmethod
    def create_default_provider(tools: List[BaseTool], node_uid: str = "default") -> PhaseProvider:
        """
        Create a default phase provider for simple scenarios.
        
        Args:
            tools: Available tools
            node_uid: Node identifier
            
        Returns:
            Default phase provider implementation
        """
        return DefaultPhaseProvider(tools, node_uid)
    
    @staticmethod
    def create_orchestrator_provider(
        node: 'OrchestratorNode',
        thread_id: str,
        tools: List[BaseTool]
    ) -> PhaseProvider:
        """
        Create an orchestrator-specific phase provider.
        
        Args:
            node: Orchestrator node instance
            thread_id: Current thread ID
            tools: Available tools
            
        Returns:
            Orchestrator phase provider implementation
        """
        # Import here to avoid circular dependency
        from ...orchestrator.orchestrator_phase_provider import OrchestratorPhaseProvider
        return OrchestratorPhaseProvider(node, thread_id, tools)
