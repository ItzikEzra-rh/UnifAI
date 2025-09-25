"""
Phase management system for agents.

This module contains all phase-related components:
- Phase definitions and protocols
- Phase providers (simple, unified, extensible)
- Validation models and contexts
- Phase-specific guidance and tools
"""

# Core phase models and protocols
from .models import (
    ValidationSeverity,
    ValidationIssue, 
    ValidationResult,
    PhaseValidationContext
)

from .phase_definition import (
    PhaseValidator,
    PhaseDefinition,
    PhaseSystem
)

from .phase_protocols import (
    PhaseState,
    WorkPlanStatus,
    PhaseContextProvider,
    PhaseToolProvider,
    PhaseTransitionPolicy,
    create_phase_state,
    create_work_plan_status
)

# Phase providers
from .unified_phase_provider import (
    PhaseProvider,
    BasePhaseProvider
)

from .simple_phase_provider import PhaseProvider as SimplePhaseProvider

from .extensible_phases import (
    PhaseRegistry,
    ExtensiblePhaseProvider
)

from .flexible_phase_provider import FlexiblePhaseProvider

# Utility modules
from . import phase_guidance
from . import phase_tools


__all__ = [
    # Core models
    "ValidationSeverity",
    "ValidationIssue", 
    "ValidationResult",
    "PhaseValidationContext",
    
    # Phase definitions
    "PhaseValidator",
    "PhaseDefinition", 
    "PhaseSystem",
    
    # Phase protocols
    "PhaseState",
    "WorkPlanStatus", 
    "PhaseContextProvider",
    "PhaseToolProvider",
    "PhaseTransitionPolicy",
    "create_phase_state",
    "create_work_plan_status",
    
    # Phase providers
    "PhaseProvider",
    "BasePhaseProvider",
    "SimplePhaseProvider",
    "PhaseRegistry",
    "ExtensiblePhaseProvider", 
    "FlexiblePhaseProvider",
    
    # Utility modules
    "phase_guidance",
    "phase_tools",
]
