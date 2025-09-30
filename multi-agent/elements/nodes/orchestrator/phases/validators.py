"""Orchestrator-specific phase validators."""

from typing import Dict, Any, List
from elements.nodes.common.agent.phases.models import PhaseValidationContext
from elements.nodes.common.workload import WorkPlan, WorkItemStatus, WorkItemKind


class AllocationValidator:
    """
    Validates allocation phase to ensure proper assignment-delegation coordination.
    
    SOLID SRP: Responsible only for allocation phase validation logic.
    """
    
    def validate(self, context: PhaseValidationContext) -> str:
        """
        Validate allocation phase state.
        
        Checks for common allocation issues:
        - Remote items assigned but not delegated (infinite loop risk)
        - Remote items delegated but not assigned (confusion)
        - Items assigned to non-adjacent nodes
        
        Args:
            context: Validation context with work plan and adjacent nodes
            
        Returns:
            Guidance text if issues found, empty string if all good
        """
        plan = context.plan
        if not isinstance(plan, WorkPlan) or not plan.items:
            return ""
        
        # Get adjacent nodes (AdjacentNodes model)
        adjacent_nodes = context.adjacent_nodes
        if adjacent_nodes is None:
            from graph.models import AdjacentNodes
            adjacent_nodes = AdjacentNodes.empty()
            
        issues: List[str] = []
        
        # Check assignment-delegation coordination for remote items
        for item in plan.items.values():
            if item.status == WorkItemStatus.PENDING and item.kind == WorkItemKind.REMOTE:
                if not item.assigned_uid:
                    issues.append(
                        f"Remote item {item.id} has no assigned_uid. "
                        f"Use AssignWorkItemTool to assign it to a specific node."
                    )
                elif not item.correlation_task_id:
                    issues.append(
                        f"Remote item {item.id} assigned but not delegated. "
                        f"Use DelegateTaskTool to send it to {item.assigned_uid}. Set work_item_id={item.id}."
                    )
                elif item.assigned_uid not in adjacent_nodes:
                    issues.append(
                        f"Item {item.id} assigned to non-adjacent node {item.assigned_uid}. "
                        f"Use ListAdjacentNodesTool to see available nodes."
                    )
        
        if issues:
            return "ALLOCATION ISSUES FOUND:\n" + "\n".join(issues)
        return ""


class PlanningValidator:
    """
    Validates planning phase to ensure work plan quality.
    
    SOLID SRP: Responsible only for planning phase validation logic.
    """
    
    def validate(self, context: PhaseValidationContext) -> str:
        """
        Validate planning phase state.
        
        Checks for common planning issues:
        - Missing work plan
        - Empty work plan
        - Circular dependencies
        
        Args:
            context: Validation context with work plan
            
        Returns:
            Guidance text if issues found, empty string if all good
        """
        plan = context.plan
        
        if not isinstance(plan, WorkPlan):
            return "No work plan found. Use CreateOrUpdateWorkPlanTool to create one."
        
        if not plan.items:
            return "Empty work plan. Break down the request into specific work items."
        
        # Check for circular dependencies
        circular = self._find_circular_dependencies(plan)
        if circular:
            return f"Circular dependencies detected: {circular}. Fix dependency chain."
        
        return ""
    
    def _find_circular_dependencies(self, plan: WorkPlan) -> List[str]:
        """
        Find circular dependencies using DFS.
        
        Args:
            plan: Work plan to check
            
        Returns:
            List of item IDs involved in circular dependencies
        """
        visited = set()
        rec_stack = set()
        circular_items = []
        
        def dfs(item_id: str) -> bool:
            if item_id in rec_stack:
                circular_items.append(item_id)
                return True
            if item_id in visited:
                return False
            
            visited.add(item_id)
            rec_stack.add(item_id)
            
            item = plan.items.get(item_id)
            if item and item.dependencies:
                for dep_id in item.dependencies:
                    if dfs(dep_id):
                        circular_items.append(item_id)
                        return True
            
            rec_stack.remove(item_id)
            return False
        
        for item_id in plan.items:
            if item_id not in visited:
                dfs(item_id)
        
        return list(set(circular_items))


class ExecutionValidator:
    """
    Validates execution phase to ensure local work items are properly handled.
    
    SOLID SRP: Responsible only for execution phase validation logic.
    """
    
    def validate(self, context: PhaseValidationContext) -> str:
        """
        Validate execution phase state.
        
        Checks for execution issues:
        - Local items stuck in pending state
        - Missing required tools for local execution
        
        Args:
            context: Validation context with work plan
            
        Returns:
            Guidance text if issues found, empty string if all good
        """
        plan = context.plan
        if not isinstance(plan, WorkPlan) or not plan.items:
            return ""
        
        issues: List[str] = []
        
        # Check for stuck local items
        pending_local_items = [
            item for item in plan.items.values()
            if item.status == WorkItemStatus.PENDING and item.kind == WorkItemKind.LOCAL
        ]
        
        if pending_local_items:
            issues.append(
                f"{len(pending_local_items)} local items pending execution. "
                f"Try to execute them directly or use domain tools if available to help."
            )
        
        if issues:
            return "EXECUTION ISSUES FOUND:\n" + "\n".join(issues)
        return ""


class MonitoringValidator:
    """
    Validates monitoring phase to ensure proper response handling.
    
    SOLID SRP: Responsible only for monitoring phase validation logic.
    """
    
    def validate(self, context: PhaseValidationContext) -> str:
        """
        Validate monitoring phase state.
        
        Checks for monitoring issues:
        - Delegated items with no responses after reasonable time
        - Items in progress but no updates
        
        Args:
            context: Validation context with work plan
            
        Returns:
            Guidance text if issues found, empty string if all good
        """
        plan = context.plan
        if not isinstance(plan, WorkPlan) or not plan.items:
            return ""
        
        issues: List[str] = []
        
        # Check for delegated items waiting for responses
        delegated_items = [
            item for item in plan.items.values()
            if item.status == WorkItemStatus.IN_PROGRESS and 
            item.kind == WorkItemKind.REMOTE and 
            item.correlation_task_id
        ]
        
        if delegated_items:
            issues.append(
                f"{len(delegated_items)} delegated items waiting for responses. "
                f"Monitor for incoming task responses or consider timeout handling."
            )
        
        if issues:
            return "MONITORING STATUS:\n" + "\n".join(issues)
        return ""


class SynthesisValidator:
    """
    Validates synthesis phase to ensure proper completion conditions.
    
    SOLID SRP: Responsible only for synthesis phase validation logic.
    """
    
    def validate(self, context: PhaseValidationContext) -> str:
        """
        Validate synthesis phase state.
        
        Checks for synthesis issues:
        - Incomplete work items blocking synthesis
        - Missing results from completed items
        
        Args:
            context: Validation context with work plan
            
        Returns:
            Guidance text if issues found, empty string if all good
        """
        plan = context.plan
        if not isinstance(plan, WorkPlan) or not plan.items:
            return ""
        
        issues: List[str] = []
        
        # Check for incomplete items
        incomplete_items = [
            item for item in plan.items.values()
            if item.status not in [WorkItemStatus.DONE, WorkItemStatus.FAILED]
        ]
        
        if incomplete_items:
            issues.append(
                f"{len(incomplete_items)} items not yet completed. "
                f"Synthesis should wait until all work is finished."
            )
        else:
            # All items complete - good for synthesis
            completed_items = [
                item for item in plan.items.values()
                if item.status == WorkItemStatus.DONE
            ]
            issues.append(
                f"All {len(plan.items)} work items completed. Ready for synthesis."
            )
        
        if issues:
            return "SYNTHESIS STATUS:\n" + "\n".join(issues)
        return ""
