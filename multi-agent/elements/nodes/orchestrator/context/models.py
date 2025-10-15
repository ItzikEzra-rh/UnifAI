"""
Pydantic models for orchestrator context.

Defines structured data models for context-aware orchestration including
cycle triggers, intent classification, health metrics, and history tracking.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CycleTriggerReason(Enum):
    """Why an orchestration cycle was triggered."""
    NEW_REQUEST = "new_request"
    RESPONSE_ARRIVED = "response_arrived"
    FOLLOW_UP_REQUEST = "follow_up_request"
    RETRY = "retry"
    PHASE_TRANSITION = "phase_transition"
    MANUAL = "manual"


class CycleTrigger(BaseModel):
    """Context about why this orchestration cycle is running."""
    reason: CycleTriggerReason
    description: str = Field(..., description="Human-readable explanation")
    
    # Context-specific details
    new_user_message: Optional[str] = Field(None, description="For NEW_REQUEST, FOLLOW_UP_REQUEST")
    response_task_ids: List[str] = Field(default_factory=list, description="For RESPONSE_ARRIVED")
    changed_items: List[str] = Field(default_factory=list, description="Items affected")
    
    def to_summary(self) -> str:
        """Format trigger as string for context display."""
        if self.reason == CycleTriggerReason.NEW_REQUEST:
            return f"🆕 NEW REQUEST: {self.new_user_message}"
        elif self.reason == CycleTriggerReason.RESPONSE_ARRIVED:
            count = len(self.response_task_ids)
            items = ', '.join(self.changed_items[:3])
            more = f" (+{len(self.changed_items) - 3} more)" if len(self.changed_items) > 3 else ""
            return f"📥 RESPONSES ARRIVED: {count} response(s) for items: {items}{more}"
        elif self.reason == CycleTriggerReason.FOLLOW_UP_REQUEST:
            return f"🔄 FOLLOW-UP: {self.new_user_message}"
        elif self.reason == CycleTriggerReason.RETRY:
            return f"🔁 RETRY: {self.description}"
        elif self.reason == CycleTriggerReason.PHASE_TRANSITION:
            return f"⚡ PHASE TRANSITION: {self.description}"
        else:
            return f"🔔 {self.reason.value.upper()}: {self.description}"


class FutilityIndicator(BaseModel):
    """Detects repeated failures and futility patterns."""
    item_id: str
    issue_type: str = Field(..., description="repeated_failure, stuck_delegation, circular_dependency")
    occurrences: int
    description: str
    suggested_action: str


class ProgressMetrics(BaseModel):
    """Progress tracking across orchestration cycles."""
    total_cycles: int = 0
    cycles_without_completion: int = 0
    items_completed_this_cycle: int = 0
    items_blocked: int = 0
    
    # Trend indicators
    is_stalled: bool = Field(default=False, description="No progress for N cycles")
    is_regressing: bool = Field(default=False, description="Failed items increasing")
    
    def to_summary(self) -> str:
        """Format progress metrics as string."""
        if self.is_stalled:
            return f"⚠️ STALLED: No progress for {self.cycles_without_completion} cycles"
        if self.is_regressing:
            return f"📉 REGRESSING: Items failing, may need pivot"
        if self.items_completed_this_cycle > 0:
            return f"✅ PROGRESSING: {self.items_completed_this_cycle} item(s) completed this cycle"
        return f"🔄 WORKING: {self.total_cycles} cycle(s) so far"


class WorkPlanHealth(BaseModel):
    """Health and progress indicators for work plan."""
    futility_indicators: List[FutilityIndicator] = Field(default_factory=list)
    progress_metrics: ProgressMetrics
    blocked_items_analysis: List[str] = Field(
        default_factory=list,
        description="Human-readable explanations of blocked items"
    )
    
    # Quick flags
    has_critical_issues: bool = False
    needs_pivot: bool = False
    needs_user_input: bool = False
    
    def to_summary(self) -> str:
        """Format health status as string."""
        lines = []
        
        # Progress
        lines.append(f"Progress: {self.progress_metrics.to_summary()}")
        
        # Critical issues
        if self.has_critical_issues:
            lines.append("\n⚠️ CRITICAL ISSUES DETECTED:")
            for indicator in self.futility_indicators[:3]:
                lines.append(f"  - {indicator.item_id}: {indicator.description}")
                lines.append(f"    Suggestion: {indicator.suggested_action}")
        
        # Blocked items
        if self.blocked_items_analysis:
            lines.append("\n🚫 BLOCKED ITEMS:")
            for analysis in self.blocked_items_analysis[:3]:
                lines.append(f"  - {analysis}")
        
        # Recommendations
        if self.needs_pivot:
            lines.append("\n💡 RECOMMENDATION: Consider pivoting strategy or marking futile items as FAILED")
        if self.needs_user_input:
            lines.append("\n💡 RECOMMENDATION: May need to ask user for clarification or additional information")
        
        return "\n".join(lines) if lines else "✅ No health issues detected"


class RequestIntent(BaseModel):
    """Classification of user request intent."""
    is_new_task: bool = True
    is_follow_up: bool = False
    is_clarification: bool = False
    is_refinement: bool = False
    is_expansion: bool = False
    
    # Relationships
    relates_to_items: List[str] = Field(
        default_factory=list,
        description="Which work items are related"
    )
    replaces_item: Optional[str] = Field(None, description="Replaces/supersedes this item")
    depends_on_items: List[str] = Field(
        default_factory=list,
        description="Requires these to be done first"
    )
    
    # Context
    original_query: str
    interpreted_intent: str = Field(..., description="Interpreted meaning")
    
    def to_summary(self) -> str:
        """Format intent as string."""
        if self.is_new_task and not self.is_follow_up:
            return f"🆕 NEW TASK: {self.interpreted_intent}"
        elif self.is_follow_up:
            items = ', '.join(self.relates_to_items[:2])
            more = f" (+{len(self.relates_to_items) - 2} more)" if len(self.relates_to_items) > 2 else ""
            return f"🔄 FOLLOW-UP on [{items}{more}]: {self.interpreted_intent}"
        elif self.is_refinement:
            item = self.relates_to_items[0] if self.relates_to_items else "unknown"
            return f"🔧 REFINEMENT of [{item}]: {self.interpreted_intent}"
        elif self.is_expansion:
            return f"📈 EXPANSION: {self.interpreted_intent}"
        else:
            return f"💬 CLARIFICATION: {self.interpreted_intent}"


class PhaseTransition(BaseModel):
    """Record of a phase transition."""
    from_phase: str
    to_phase: str
    timestamp: str
    reason: str = ""
    actions_taken: List[str] = Field(default_factory=list)


class PhaseHistory(BaseModel):
    """History of recent phase activity."""
    current_cycle_transitions: List[PhaseTransition] = Field(default_factory=list)
    phase_iteration_counts: Dict[str, int] = Field(default_factory=dict)
    last_n_cycles: List[dict] = Field(
        default_factory=list,
        description="Last 3 cycles summary"
    )
    
    def to_summary(self) -> str:
        """Format history as string."""
        if not self.current_cycle_transitions and not self.phase_iteration_counts:
            return "Starting first cycle"
        
        lines = ["Recent Phase Activity:"]
        
        # Current cycle path
        if self.current_cycle_transitions:
            path = " → ".join([t.to_phase for t in self.current_cycle_transitions])
            lines.append(f"  Current cycle path: {path}")
        
        # Iteration counts (only show phases with >1 iteration)
        if self.phase_iteration_counts:
            counts = ', '.join([f"{p}={c}" for p, c in self.phase_iteration_counts.items() if c > 1])
            if counts:
                lines.append(f"  Phase iterations: {counts}")
        
        return "\n".join(lines)


class OrchestratorContext(BaseModel):
    """Complete context for orchestrator cycle execution."""
    
    # Why are we running?
    trigger: CycleTrigger
    
    # What does user want?
    request_intent: Optional[RequestIntent] = None
    
    # How's the work plan doing?
    health: WorkPlanHealth
    
    # What happened before?
    history: PhaseHistory
    
    # Current state (from existing PhaseState)
    phase_state: Any = Field(None, description="PhaseState from existing system")
    
    def format_context(self, work_plan_snapshot: str) -> str:
        """
        Format complete context including work plan in single message.
        
        Combines orchestrator context and work plan into one coherent message
        for presentation to the orchestrator.
        
        Args:
            work_plan_snapshot: Pre-formatted work plan snapshot string
        
        Returns:
            Complete formatted context string
        """
        sections = [
            "="*80,
            "📊 ORCHESTRATION CYCLE CONTEXT",
            "="*80,
            "",
            "🎯 WHY THIS CYCLE:",
            self.trigger.to_summary(),
            ""
        ]
        
        if self.request_intent:
            sections.extend([
                "💭 REQUEST INTENT:",
                self.request_intent.to_summary(),
                ""
            ])
        
        sections.extend([
            "🏥 WORK PLAN HEALTH:",
            self.health.to_summary(),
            "",
            "📜 HISTORY:",
            self.history.to_summary(),
            "",
            "="*80,
            "",
            "📋 CURRENT WORK PLAN:",
            work_plan_snapshot,
            "",
            "="*80
        ])
        
        return "\n".join(sections)

