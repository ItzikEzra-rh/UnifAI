"""
Orchestrator context system for rich, context-aware orchestration.

Provides specialized analyzers and models for understanding:
- Why cycles are triggered
- User intent (new task vs follow-up)
- Work plan health (futility, stalls, blocked items)
- Progress metrics across cycles
- Phase transition history
"""

from .models import (
    CycleTriggerReason,
    CycleTrigger,
    FutilityIndicator,
    ProgressMetrics,
    WorkPlanHealth,
    RequestIntent,
    PhaseTransition,
    PhaseHistory,
    OrchestratorContext
)

from .analyzers import (
    IntentClassifier,
    HealthAnalyzer,
    ProgressTracker
)

from .builder import OrchestratorContextBuilder

__all__ = [
    # Enums
    'CycleTriggerReason',
    
    # Models
    'CycleTrigger',
    'FutilityIndicator',
    'ProgressMetrics',
    'WorkPlanHealth',
    'RequestIntent',
    'PhaseTransition',
    'PhaseHistory',
    'OrchestratorContext',
    
    # Analyzers
    'IntentClassifier',
    'HealthAnalyzer',
    'ProgressTracker',
    
    # Builder
    'OrchestratorContextBuilder',
]

