"""
Clean Pydantic models for phase definitions.

Provides structured, type-safe phase configuration.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from elements.tools.common.base_tool import BaseTool


class PhaseDefinition(BaseModel):
    """
    Clean definition of a single execution phase.
    
    Contains all phase-specific configuration in one place.
    """
    name: str = Field(..., description="Phase name (e.g., 'planning', 'execution')")
    description: str = Field(..., description="What this phase does")
    tools: List[BaseTool] = Field(default_factory=list, description="Actual tool objects for this phase")
    guidance: str = Field(..., description="LLM guidance for this phase")
    
    class Config:
        arbitrary_types_allowed = True  # Allow BaseTool objects
    
    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to this phase."""
        if tool not in self.tools:
            self.tools.append(tool)
    
    def add_tools(self, tools: List[BaseTool]) -> None:
        """Add multiple tools to this phase."""
        for tool in tools:
            self.add_tool(tool)
    
    def get_tool_names(self) -> List[str]:
        """Get list of tool names for debugging/logging."""
        return [tool.name for tool in self.tools]


class PhaseSystem(BaseModel):
    """
    Complete phase system definition.
    
    Contains all phases and their configurations for a specific provider.
    """
    name: str = Field(..., description="Name of this phase system (e.g., 'orchestrator')")
    description: str = Field(..., description="What this phase system does")
    phases: List[PhaseDefinition] = Field(default_factory=list, description="All phases in execution order")
    
    def add_phase(self, phase: PhaseDefinition) -> None:
        """Add a phase to this system."""
        self.phases.append(phase)
    
    def get_phase(self, name: str) -> Optional[PhaseDefinition]:
        """Get a phase by name."""
        for phase in self.phases:
            if phase.name == name:
                return phase
        return None
    
    def get_phase_names(self) -> List[str]:
        """Get list of all phase names in order."""
        return [phase.name for phase in self.phases]
    
    def get_tools_for_phase(self, phase_name: str) -> List[BaseTool]:
        """Get actual tool objects for a specific phase."""
        phase = self.get_phase(phase_name)
        return phase.tools if phase else []
    
    def get_guidance_for_phase(self, phase_name: str) -> str:
        """Get guidance text for a specific phase."""
        phase = self.get_phase(phase_name)
        return phase.guidance if phase else ""
