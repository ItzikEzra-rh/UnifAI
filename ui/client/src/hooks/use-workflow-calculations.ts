import { useMemo } from "react";
import { WorkflowBlueprint } from "@/api/agentic";

interface WorkflowWithUsage extends WorkflowBlueprint {
  usageCount: number;
  isCurrentlyActive: boolean;
}

export function useWorkflowCalculations(
  workflows: WorkflowBlueprint[],
  activeSessions: string[],
  blueprintSessionCounts: Record<string, number>
) {
  const mostUsedWorkflows = useMemo<WorkflowWithUsage[]>(() => {
    return workflows
      .map((workflow) => {
        const sessionCount = blueprintSessionCounts[workflow.blueprint_id] ?? 0;
        const isCurrentlyActive =
          Array.isArray(activeSessions) &&
          activeSessions.includes(workflow.blueprint_id);
        const usageCount =
          sessionCount > 0 ? sessionCount : isCurrentlyActive ? 1 : 0;
        return {
          ...workflow,
          usageCount,
          isCurrentlyActive,
        };
      })
      .filter((workflow) => workflow.usageCount > 0)
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, 5);
  }, [workflows, activeSessions, blueprintSessionCounts]);

  const unusedWorkflows = useMemo(() => {
    return workflows.filter(
      (workflow) => !activeSessions.includes(workflow.blueprint_id)
    );
  }, [workflows, activeSessions]);

  return {
    mostUsedWorkflows,
    unusedWorkflows,
  };
}

