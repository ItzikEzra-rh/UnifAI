import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import {
  fetchAgenticStats,
  fetchBlueprints,
  fetchActiveSessions,
  fetchAllResources,
  fetchBlueprintSessionCounts,
  fetchResourceCategories,
} from "@/api/agentic";

export function useAgenticData() {
  const { user } = useAuth();
  const userId = user?.username || "default";

  // Use aggregated stats endpoint for optimal performance
  const agenticStats = useQuery({
    queryKey: ["agenticStats", userId],
    queryFn: () => fetchAgenticStats(userId),
    staleTime: 0,
  });

  // Individual queries for granular data when needed by components
  const workflows = useQuery({
    queryKey: ["blueprints", userId],
    queryFn: () => fetchBlueprints(userId),
    staleTime: 0,
  });

  const activeSessions = useQuery({
    queryKey: ["activeSessions", userId],
    queryFn: () => fetchActiveSessions(userId),
    staleTime: 0,
  });

  // Fetch blueprintSessionCounts separately for components that need it independently
  // Note: This is also included in agenticStats, but kept separate for granular access
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
      // Prefer aggregated stats if available, otherwise use individual query
      data: agenticStats.data?.blueprintSessionCounts ?? blueprintSessionCounts.data ?? {},
      isLoading: !agenticStats.data ? blueprintSessionCounts.isLoading : false,
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
      (!agenticStats.data && blueprintSessionCounts.isLoading) ||
      resources.isLoading ||
      resourceCategories.isLoading,
  };
}

