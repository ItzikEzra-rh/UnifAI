"""
Unified phase provider following SOLID principles.

This module provides a single, cohesive interface for all phase-related concerns,
using clean Pydantic models for phase definitions with validation support.
"""

from typing import Protocol, List, Optional, Any
from abc import ABC, abstractmethod
from elements.tools.common.base_tool import BaseTool
from .phase_definition import PhaseSystem, PhaseDefinition
from .phase_protocols import PhaseState

# Import for typing - avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import PhaseValidationContext


class PhaseProvider(Protocol):
    """
    Clean, unified protocol for all phase-related concerns.
    
    Uses Pydantic models for type-safe, well-defined phase management.
    """
    
    def get_phase_system(self) -> PhaseSystem:
        """Get the complete phase system definition."""
        ...
    
    def get_phase_context(self) -> PhaseState:
        """Get current phase context for decision making."""
        ...
    
    def get_tools_for_phase(self, phase_name: str) -> List[BaseTool]:
        """Get actual tool objects for the given phase."""
        ...
    
    def get_phase_guidance(self, phase_name: str) -> str:
        """Get guidance text for the given phase."""
        ...
    
    def decide_next_phase(
        self,
        current_phase: str,
        context: PhaseState,
        observations: List[Any]
    ) -> str:
        """Decide the next execution phase based on current state."""
        ...
    
    def get_supported_phases(self) -> List[str]:
        """Get list of phase names supported by this provider."""
        ...


class BasePhaseProvider(ABC):
    """
    Clean abstract base class for phase providers.
    
    Uses Pydantic models for well-defined, type-safe phase management.
    Each subclass defines its complete phase system using PhaseSystem model.
    """
    
    def __init__(self, tools: List[BaseTool]):
        """
        Initialize with available tools.
        
        Args:
            tools: All available tools that can be assigned to phases
        """
        self._tools = tools
        self._phase_system = self._create_phase_system()
    
    @abstractmethod
    def _create_phase_system(self) -> PhaseSystem:
        """
        Create the complete phase system for this provider.
        
        Subclasses must implement this to define their phases using
        clean Pydantic models with actual tool objects.
        
        Returns:
            PhaseSystem with all phases and their configurations
        """
        pass
    
    def get_phase_system(self) -> PhaseSystem:
        """Get the complete phase system definition."""
        return self._phase_system
    
    def get_supported_phases(self) -> List[str]:
        """Get list of phase names supported by this provider."""
        return self._phase_system.get_phase_names()
    
    def get_tools_for_phase(self, phase_name: str) -> List[BaseTool]:
        """Get actual tool objects for the given phase."""
        return self._phase_system.get_tools_for_phase(phase_name)
    
    def get_phase_guidance(self, phase_name: str) -> str:
        """Get guidance text for the given phase."""
        return self._phase_system.get_guidance_for_phase(phase_name)
    
    @abstractmethod
    def _build_validation_context(self, phase_name: str) -> "PhaseValidationContext":
        """
        Build validation context for the given phase.
        
        This is the extension point for providers to add their specific
        context data (e.g., work plan, adjacent nodes, etc.).
        
        Args:
            phase_name: Name of the phase to validate
            
        Returns:
            PhaseValidationContext with provider-specific data
        """
        pass
    
    def get_phase_validation(self, phase_name: str) -> str:
        """
        Get validation guidance for the given phase.
        
        SRP: This method is responsible only for validation concerns.
        
        Args:
            phase_name: Name of the phase to validate
            
        Returns:
            Validation guidance text, empty if no issues found
        """
        phase = self._phase_system.get_phase(phase_name)
        if not phase:
            return ""
            
        try:
            context = self._build_validation_context(phase_name)
            return phase.run_validators(context)
        except Exception as e:
            print(f"Validation error in phase '{phase_name}': {e}")
            return ""
    
    def build_phase_prompt(self, phase_name: str) -> str:
        """
        Build complete phase prompt with base guidance and validation.
        
        SRP: This method is responsible only for composing guidance.
        
        Args:
            phase_name: Name of the phase
            
        Returns:
            Complete prompt with base guidance and validation guidance
        """
        base_guidance = self.get_phase_guidance(phase_name)
        validation_guidance = self.get_phase_validation(phase_name)
        
        if validation_guidance:
            return f"{base_guidance}\n\n{validation_guidance}"
        return base_guidance
    
    @abstractmethod
    def get_phase_context(self) -> PhaseState:
        """Get current phase context - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def decide_next_phase(
        self,
        current_phase: str,
        context: PhaseState,
        observations: List[Any]
    ) -> str:
        """Decide next phase - must be implemented by subclasses."""
        pass


