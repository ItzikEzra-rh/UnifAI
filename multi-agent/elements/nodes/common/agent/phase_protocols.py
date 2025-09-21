"""
Phase-related protocols and models for agent strategies.

This module defines typed interfaces for phase context and tool provision,
replacing generic dictionaries with proper abstractions that strategies
can depend on without coupling to specific implementations.

Design Principles:
- Protocol-based: Strategies depend on abstractions, not concrete types
- Type Safety: Replace Dict[str, Any] with structured models
- Single Responsibility: Each protocol has one clear purpose
- Testability: Easy to mock and test with protocols
"""

from typing import Protocol, Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from elements.tools.common.base_tool import BaseTool

# Import ExecutionPhase for stronger typing
from .constants import ExecutionPhase

# Forward declaration for AgentObservation
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..primitives import AgentObservation


# =============================================================================
# PHASE STATE MODELS
# =============================================================================

@dataclass(frozen=True)
class WorkPlanStatus:
    """Immutable snapshot of work plan status."""
    total_items: int
    pending_items: int
    in_progress_items: int
    waiting_items: int
    done_items: int
    failed_items: int
    blocked_items: int
    has_local_ready: bool
    has_remote_waiting: bool
    is_complete: bool


@dataclass(frozen=True)
class PhaseState:
    """
    Immutable state information for phase decision making.
    
    This replaces the generic Dict[str, Any] context with a typed model
    that strategies can depend on without knowing implementation details.
    """
    work_plan_status: Optional[WorkPlanStatus] = None
    thread_id: Optional[str] = None
    node_uid: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None


# =============================================================================
# PROTOCOLS
# =============================================================================

class PhaseContextProvider(Protocol):
    """
    Protocol for providing phase context to strategies.
    
    This abstraction allows strategies to get the information they need
    for phase decisions without depending on specific service implementations.
    """
    
    def get_phase_context(self) -> PhaseState:
        """
        Get current phase context for decision making.
        
        Returns:
            PhaseState with current work plan status and context
        """
        ...


class PhaseToolProvider(Protocol):
    """
    Protocol for providing phase-specific tools to strategies.
    
    This abstraction separates tool categorization logic from strategies,
    making both more testable and maintainable.
    """
    
    def get_tools_for_phase(self, phase: ExecutionPhase) -> List[BaseTool]:
        """
        Get tools appropriate for the given phase.
        
        Args:
            phase: The execution phase enum
            
        Returns:
            List of tools suitable for this phase
        """
        ...
    
    def get_all_phase_tools(self) -> Dict[ExecutionPhase, List[BaseTool]]:
        """
        Get all phase-to-tools mappings.
        
        Returns:
            Dictionary mapping execution phases to tool lists
        """
        ...


class PhaseTransitionPolicy(Protocol):
    """
    Protocol for determining phase transitions in strategies.
    
    This abstraction allows nodes to inject custom phase transition logic
    into strategies, keeping the strategy focused on execution while
    externalizing phase decision-making.
    """
    
    def decide(
        self,
        *,
        state: PhaseState,
        current: ExecutionPhase,
        observations: List['AgentObservation']
    ) -> ExecutionPhase:
        """
        Decide the next execution phase based on current state.
        
        Args:
            state: Current phase state with work plan status
            current: Current execution phase
            observations: Recent agent observations
            
        Returns:
            The next execution phase to transition to
        """
        ...


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_work_plan_status(
    *,
    total_items: int = 0,
    pending_items: int = 0,
    in_progress_items: int = 0,
    waiting_items: int = 0,
    done_items: int = 0,
    failed_items: int = 0,
    blocked_items: int = 0,
    has_local_ready: bool = False,
    has_remote_waiting: bool = False,
    is_complete: bool = False
) -> WorkPlanStatus:
    """
    Create a WorkPlanStatus with explicit parameters.
    
    This function provides a clean way to create status objects
    with clear parameter names and validation.
    """
    return WorkPlanStatus(
        total_items=total_items,
        pending_items=pending_items,
        in_progress_items=in_progress_items,
        waiting_items=waiting_items,
        done_items=done_items,
        failed_items=failed_items,
        blocked_items=blocked_items,
        has_local_ready=has_local_ready,
        has_remote_waiting=has_remote_waiting,
        is_complete=is_complete
    )


def create_phase_state(
    work_plan_status: Optional[WorkPlanStatus] = None,
    thread_id: Optional[str] = None,
    node_uid: Optional[str] = None,
    **additional_context: Any
) -> PhaseState:
    """
    Create a PhaseState with optional additional context.
    
    Args:
        work_plan_status: Current work plan status
        thread_id: Current thread ID
        node_uid: Current node UID
        **additional_context: Any additional context data
        
    Returns:
        PhaseState with provided information
    """
    return PhaseState(
        work_plan_status=work_plan_status,
        thread_id=thread_id,
        node_uid=node_uid,
        additional_context=additional_context if additional_context else None
    )
