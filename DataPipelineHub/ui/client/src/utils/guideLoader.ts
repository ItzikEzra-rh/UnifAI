// Guide loader utility
// Loads YAML guide files and converts them to structured data
import yaml from "js-yaml";

export interface Guide {
  guide_title: string;
  title: string;
  description?: string;
  category: string;
  section: string;
  order: number;
  steps: Array<{
    step: number;
    title: string;
    body: string;
  }>;
}

export interface GuidesByCategory {
  [category: string]: Guide[];
}

// Parse YAML using js-yaml library
export const parseYAML = (yamlText: string): Guide | null => {
  try {
    const parsed = yaml.load(yamlText) as any;
    
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    
    const guide: Guide = {
      guide_title: parsed.guide_title || parsed.title || "",
      title: parsed.title || "",
      description: parsed.description,
      category: parsed.category || "",
      section: parsed.section || "",
      order: parsed.order || 0,
      steps: (parsed.steps || []).map((step: any) => ({
        step: step.step || 0,
        title: step.title || "",
        body: step.body || "",
      })),
    };
    
    // Validate guide structure
    if (guide.guide_title && guide.category && guide.section && guide.steps.length > 0) {
      return guide;
    }
    
    return null;
  } catch (error) {
    console.error("Error parsing YAML:", error);
    return null;
  }
};

// Load a guide from a URL
export const loadGuide = async (url: string): Promise<Guide | null> => {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return null;
    }
    const yamlText = await response.text();
    return parseYAML(yamlText);
  } catch (error) {
    console.error(`Error loading guide from ${url}:`, error);
    return null;
  }
};

// Load all guides for a section
export const loadGuidesForSection = async (section: string, category?: string): Promise<GuidesByCategory> => {
  // Define guide paths - in production, this could be dynamic or come from an API
  const guidePaths: { [key: string]: { [category: string]: string[] } } = {
    "agentic-inventory": {
      "providers": [
        "/guides/agentic-inventory/providers/google-mcp-provider.yaml",
      ],
      "conditions": [],
      "llms": [],
      "nodes": [],
      "retrievers": [],
      "tools": [],
    },
    "slack-integration": {},
    "documents": {},
    "agentic-ai-workflows": {},
  };
  
  const sectionPaths = guidePaths[section] || {};
  const guides: Guide[] = [];
  
  // If a specific category is requested, only load that category
  const categoriesToLoad = category 
    ? { [category]: sectionPaths[category] || [] }
    : sectionPaths;
  
  // Load all guides in parallel
  const allPaths: string[] = [];
  Object.values(categoriesToLoad).forEach((paths) => {
    allPaths.push(...paths);
  });
  
  const results = await Promise.all(
    allPaths.map((path) => loadGuide(path))
  );
  
  // Filter out null results and group by category
  results.forEach((guide) => {
    if (guide && guide.section === section) {
      guides.push(guide);
    }
  });
  
  // Group by category and sort
  const grouped: GuidesByCategory = {};
  guides
    .sort((a, b) => a.order - b.order)
    .forEach((guide) => {
      if (!grouped[guide.category]) {
        grouped[guide.category] = [];
      }
      grouped[guide.category].push(guide);
    });
  
  // For agentic-inventory, ensure all categories exist (even if empty)
  if (section === "agentic-inventory") {
    const allCategories = ["conditions", "llms", "nodes", "providers", "retrievers", "tools"];
    allCategories.forEach((cat) => {
      if (!grouped[cat]) {
        grouped[cat] = [];
      }
    });
  }
  
  // If a specific category was requested but has no guides, still create an empty entry
  if (category && !grouped[category]) {
    grouped[category] = [];
  }
  
  return grouped;
};

