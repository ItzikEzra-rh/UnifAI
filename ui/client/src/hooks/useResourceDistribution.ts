import { useMemo } from "react";

interface ResourceCategory {
  category: string;
  count: number;
  types: { [type: string]: number };
}

const FALLBACK_CATEGORIES = [
  "conditions",
  "llms",
  "agents",
  "providers",
  "retrievers",
  "tools",
];

export function useResourceDistribution(
  resourceCategories: string[],
  resourcesByCategory: ResourceCategory[]
) {
  const resourceDistribution = useMemo(() => {
    const allCategories =
      resourceCategories.length > 0
        ? resourceCategories.map((cat) =>
            cat.toLowerCase() === "nodes" ? "agents" : cat.toLowerCase()
          )
        : FALLBACK_CATEGORIES;

    const resourceDistributionMap = new Map(
      (resourcesByCategory || []).map((cat) => {
        const categoryKey =
          cat.category.toLowerCase() === "nodes"
            ? "agents"
            : cat.category.toLowerCase();
        return [categoryKey, { ...cat, category: categoryKey }];
      })
    );

    return allCategories.map((category) => {
      const existing = resourceDistributionMap.get(category);
      if (existing) {
        return existing;
      }
      return {
        category,
        count: 0,
        types: {},
      };
    });
  }, [resourceCategories, resourcesByCategory]);

  return resourceDistribution;
}

