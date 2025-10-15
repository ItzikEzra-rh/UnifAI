"""
Specialized analyzers for orchestrator context building.

Provides focused analysis services:
- IntentClassifier: Understands user intent
- HealthAnalyzer: Detects work plan issues
- ProgressTracker: Monitors progress metrics
"""

from typing import Optional, List
from elements.nodes.common.workload import WorkPlan, WorkItem, WorkItemStatus, WorkItemKind
from .models import (
    WorkPlanHealth,
    FutilityIndicator,
    ProgressMetrics,
    RequestIntent
)


class IntentClassifier:
    """Classifies user request intent using heuristics."""
    
    def classify(
        self, 
        user_message: str, 
        plan: Optional[WorkPlan]
    ) -> RequestIntent:
        """
        Classify user request intent based on existing work plan.
        
        Uses simple heuristics:
        - If no plan exists → new task
        - If plan exists → likely follow-up
        - Keyword matching to find related items (checks DONE items)
        
        Args:
            user_message: User's request text
            plan: Current work plan (if exists)
        
        Returns:
            RequestIntent with classification
        """
        # Check if plan exists (convert to bool explicitly)
        is_follow_up = bool(plan is not None and plan.items)
        
        relates_to_items = []
        if is_follow_up and plan:
            # Simple keyword matching to find related items
            for item in plan.items.values():
                if item.status == WorkItemStatus.DONE:
                    # Check if message references completed work
                    # Use first 3 words of title as keywords
                    keywords = item.title.split()[:3]
                    if any(word.lower() in user_message.lower() 
                           for word in keywords if len(word) > 3):  # Skip short words
                        relates_to_items.append(item.id)
        
        # Determine intent type
        is_refinement = is_follow_up and len(relates_to_items) > 0
        is_expansion = is_follow_up and len(relates_to_items) == 0
        
        return RequestIntent(
            is_new_task=not is_follow_up,
            is_follow_up=is_follow_up,
            is_clarification=False,  # Could enhance with keyword detection ("what", "explain", etc.)
            is_refinement=is_refinement,
            is_expansion=is_expansion,
            relates_to_items=relates_to_items,
            original_query=user_message,
            interpreted_intent=user_message[:100]  # Truncate for display
        )


class HealthAnalyzer:
    """Analyzes work plan health and detects issues."""
    
    def analyze(self, plan: Optional[WorkPlan]) -> WorkPlanHealth:
        """
        Analyze work plan for health indicators.
        
        Detects:
        - Repeated failures (approaching max retries)
        - Stuck delegation loops (many attempts, unprocessed responses)
        - Blocked items (dependency issues)
        
        Args:
            plan: Work plan to analyze
        
        Returns:
            WorkPlanHealth with indicators and recommendations
        """
        if not plan:
            return WorkPlanHealth(progress_metrics=ProgressMetrics())
        
        futility_indicators = []
        blocked_analysis = []
        
        # Check each item for issues
        for item in plan.items.values():
            # Repeated failures
            if item.retry_count >= item.max_retries - 1:
                futility_indicators.append(FutilityIndicator(
                    item_id=item.id,
                    issue_type="repeated_failure",
                    occurrences=item.retry_count,
                    description=f"Failed {item.retry_count} times, approaching max retries ({item.max_retries})",
                    suggested_action="Consider marking as FAILED or trying different approach"
                ))
            
            # Stuck in delegation loop
            if item.result and len(item.result.delegations) > 3:
                unprocessed = sum(1 for d in item.result.delegations if not d.processed)
                if unprocessed > 1:
                    futility_indicators.append(FutilityIndicator(
                        item_id=item.id,
                        issue_type="stuck_delegation",
                        occurrences=len(item.result.delegations),
                        description=f"{len(item.result.delegations)} delegation attempts, {unprocessed} unprocessed responses",
                        suggested_action="Review agent responses - may need different agent or approach"
                    ))
            
            # Blocked by dependencies
            if item.status == WorkItemStatus.PENDING and item.dependencies:
                completed_deps = plan.get_completed_item_ids()
                blocked_by = [dep for dep in item.dependencies if dep not in completed_deps]
                if blocked_by:
                    # Get titles of blocking items for clarity
                    blocker_titles = []
                    for dep in blocked_by:
                        dep_item = plan.items.get(dep)
                        if dep_item:
                            blocker_titles.append(f"{dep} ({dep_item.status.value})")
                        else:
                            blocker_titles.append(dep)
                    
                    blocked_analysis.append(
                        f"{item.id} blocked by: {', '.join(blocker_titles)}"
                    )
        
        # Basic progress metrics (will be enriched by ProgressTracker)
        total = len(plan.items)
        done = len(plan.get_items_by_status(WorkItemStatus.DONE))
        failed = len(plan.get_items_by_status(WorkItemStatus.FAILED))
        
        progress = ProgressMetrics(
            total_cycles=0,  # Will be set by ProgressTracker
            cycles_without_completion=0,
            items_completed_this_cycle=0,
            items_blocked=len(blocked_analysis),
            is_stalled=False,
            is_regressing=failed > done and total > 2
        )
        
        return WorkPlanHealth(
            futility_indicators=futility_indicators,
            progress_metrics=progress,
            blocked_items_analysis=blocked_analysis,
            has_critical_issues=len(futility_indicators) > 0,
            needs_pivot=progress.is_regressing,
            needs_user_input=len(blocked_analysis) > 3
        )


class ProgressTracker:
    """Tracks progress metrics across orchestration cycles."""
    
    def __init__(self):
        """Initialize progress tracker with zero state."""
        self._total_cycles = 0
        self._cycles_without_completion = 0
        self._last_done_count = 0
    
    def update(self, plan: Optional[WorkPlan]) -> ProgressMetrics:
        """
        Update and return progress metrics.
        
        Tracks:
        - Total cycles run
        - Cycles without any completion
        - Items completed this cycle
        - Stalled detection (no progress for 5+ cycles)
        
        Args:
            plan: Current work plan
        
        Returns:
            ProgressMetrics with current state
        """
        self._total_cycles += 1
        
        if not plan:
            return ProgressMetrics(
                total_cycles=self._total_cycles,
                cycles_without_completion=self._cycles_without_completion
            )
        
        # Count current done items
        done_items = plan.get_items_by_status(WorkItemStatus.DONE)
        current_done = len(done_items)
        
        # Check if we completed anything this cycle
        completed_this_cycle = max(0, current_done - self._last_done_count)
        
        if completed_this_cycle == 0:
            self._cycles_without_completion += 1
        else:
            self._cycles_without_completion = 0  # Reset on progress
        
        self._last_done_count = current_done
        
        # Detect stall (no progress for 5+ cycles)
        is_stalled = self._cycles_without_completion >= 5
        
        # Count blocked items
        blocked = 0
        if plan.items:
            for item in plan.items.values():
                if item.status == WorkItemStatus.PENDING and item.dependencies:
                    completed_deps = plan.get_completed_item_ids()
                    if not all(dep in completed_deps for dep in item.dependencies):
                        blocked += 1
        
        return ProgressMetrics(
            total_cycles=self._total_cycles,
            cycles_without_completion=self._cycles_without_completion,
            items_completed_this_cycle=completed_this_cycle,
            items_blocked=blocked,
            is_stalled=is_stalled,
            is_regressing=False  # Will be set by HealthAnalyzer
        )

