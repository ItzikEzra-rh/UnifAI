import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import {
  fetchAgenticStats,
  fetchWorkflows,
  fetchActiveSessions,
  fetchAllResources,
  fetchBlueprintSessionCounts,
  fetchResourceCategories,
} from "@/api/agentic";

export function useAgenticData() {
  const { user } = useAuth();
  const userId = user?.username || "default";

  const agenticStats = useQuery({
    queryKey: ["agenticStats", userId],
    queryFn: () => fetchAgenticStats(userId),
    staleTime: 0,
  });

  const workflows = useQuery({
    queryKey: ["workflows", userId],
    queryFn: () => fetchWorkflows(userId),
    staleTime: 0,
  });

  const activeSessions = useQuery({
    queryKey: ["activeSessions", userId],
    queryFn: () => fetchActiveSessions(userId),
    staleTime: 0,
  });

  const blueprintSessionCounts = useQuery({
    queryKey: ["blueprintSessionCounts", userId],
    queryFn: () => fetchBlueprintSessionCounts(userId),
    staleTime: 0,
  });

  const resources = useQuery({
    queryKey: ["allResources", userId],
    queryFn: () => fetchAllResources(userId),
    staleTime: 0,
  });

  const resourceCategories = useQuery({
    queryKey: ["resourceCategories"],
    queryFn: () => fetchResourceCategories(),
    staleTime: 0,
  });

  return {
    agenticStats: {
      data: agenticStats.data,
      isLoading: agenticStats.isLoading,
      error: agenticStats.error,
    },
    workflows: {
      data: workflows.data ?? [],
      isLoading: workflows.isLoading,
      error: workflows.error,
    },
    activeSessions: {
      data: activeSessions.data ?? [],
      isLoading: activeSessions.isLoading,
      error: activeSessions.error,
    },
    blueprintSessionCounts: {
      data: blueprintSessionCounts.data ?? {},
      isLoading: blueprintSessionCounts.isLoading,
      error: blueprintSessionCounts.error,
    },
    resources: {
      data: resources.data ?? [],
      isLoading: resources.isLoading,
      error: resources.error,
    },
    resourceCategories: {
      data: resourceCategories.data ?? [],
      isLoading: resourceCategories.isLoading,
      error: resourceCategories.error,
    },
    isLoading:
      agenticStats.isLoading ||
      workflows.isLoading ||
      activeSessions.isLoading ||
      blueprintSessionCounts.isLoading ||
      resources.isLoading ||
      resourceCategories.isLoading,
  };
}

