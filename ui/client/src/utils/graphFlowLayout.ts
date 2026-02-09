/**
 * Converts GraphFlow (YAML blueprint spec) to a layout-friendly structure
 * used for display (e.g. JointJS). Keeps node details for element info.
 */

import type {
  GraphFlow,
  NodeDefinition,
  PlanItem,
  LLMDefinition,
  ToolDefinition,
  RetrieverDefinition,
} from "@/components/agentic-ai/graphs/interfaces";

/** Resolved reference: display name + id for modal/details. */
export interface ResolvedElement {
  type: "llm" | "tool" | "retriever";
  name: string;
  id: string;
}

export interface LayoutNode {
  id: string;
  label: string;
  description: string | null;
  type: string;
  /** Rank/level for hierarchical layout (0 = top) */
  level: number;
  /** Element details for display (config summary) */
  elementDetails: Record<string, unknown>;
  /** Resolved refs as name + id (names for display, ids for details modal) */
  resolvedElements: ResolvedElement[];
  /** Full node definition from YAML for tooltips/details */
  nodeDefinition: NodeDefinition | null;
}

export interface LayoutEdge {
  source: string;
  target: string;
  isConditional?: boolean;
  branchKey?: string;
}

export interface GraphFlowLayoutData {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
}

function extractUidFromRef(value: string): string {
  if (typeof value === "string" && value.startsWith("$ref:")) {
    return value.substring(5);
  }
  return value;
}

/**
 * Build a short summary of element config for display (legacy).
 */
function getElementDetails(nodeDef: NodeDefinition): Record<string, unknown> {
  const details: Record<string, unknown> = {};
  const config = nodeDef?.config || {};
  if (config.llm) details.llm = config.llm;
  if (config.retriever) details.retriever = config.retriever;
  if (config.tools && Array.isArray(config.tools)) details.tools = config.tools.length;
  if (config.type) details.type = config.type;
  if (config.system_message != null) details.system_message = true;
  return details;
}

function extractRefId(value: unknown): string | null {
  if (typeof value !== "string") return null;
  return value.startsWith("$ref:") ? value.substring(5) : value;
}

/**
 * Resolve config refs to { type, name, id } using graphFlow.llms/tools/retrievers (names only for display).
 */
function getResolvedElements(graphFlow: GraphFlow, nodeDef: NodeDefinition | null): ResolvedElement[] {
  const out: ResolvedElement[] = [];
  if (!nodeDef?.config) return out;
  const config = nodeDef.config;
  const llms = graphFlow.llms || [];
  const tools = graphFlow.tools || [];
  const retrievers = graphFlow.retrievers || [];

  const llmRef = extractRefId(config.llm);
  if (llmRef) {
    const llm = llms.find((l: LLMDefinition) => extractUidFromRef(l.rid) === llmRef || l.rid === llmRef);
    out.push({ type: "llm", name: llm?.name ?? llmRef, id: llmRef });
  }
  const retrieverRef = extractRefId(config.retriever);
  if (retrieverRef) {
    const ret = retrievers.find(
      (r: RetrieverDefinition) => extractUidFromRef(r.rid) === retrieverRef || r.rid === retrieverRef
    );
    out.push({ type: "retriever", name: ret?.name ?? retrieverRef, id: retrieverRef });
  }
  const toolRefs = Array.isArray(config.tools)
    ? config.tools.map((t) => extractRefId(t)).filter((id): id is string => id != null)
    : [];
  for (const ref of toolRefs) {
    const tool = tools.find((t: ToolDefinition) => extractUidFromRef(t.rid) === ref || t.rid === ref);
    out.push({ type: "tool", name: tool?.name ?? ref, id: ref });
  }
  return out;
}

/**
 * Convert GraphFlow (same YAML structure used by the builder) to nodes and edges
 * with levels for hierarchical layout. Used by the panel graph display.
 */
export function graphFlowToLayoutData(graphFlow: GraphFlow): GraphFlowLayoutData {
  if (!graphFlow?.plan) {
    return { nodes: [], edges: [] };
  }

  const nodeMap: Record<string, NodeDefinition> = {};
  if (graphFlow.nodes) {
    graphFlow.nodes.forEach((node) => {
      nodeMap[extractUidFromRef(node.rid)] = node;
    });
  }

  const nodePredecessors: Record<string, string[]> = {};
  const nodeSuccessors: Record<string, string[]> = {};
  const nodesByLevel: Record<number, string[]> = {};
  const nodeLevel: Record<string, number> = {};

  // First pass: predecessors/successors
  graphFlow.plan.forEach((item: PlanItem) => {
    const nodeId = item.uid;
    if (item.after) {
      const predecessors = Array.isArray(item.after) ? item.after : [item.after];
      nodePredecessors[nodeId] = predecessors;
      predecessors.forEach((predId) => {
        if (!nodeSuccessors[predId]) nodeSuccessors[predId] = [];
        nodeSuccessors[predId].push(nodeId);
      });
    } else {
      nodePredecessors[nodeId] = [];
    }
  });

  // Level 0: user_question_node
  graphFlow.plan.forEach((item: PlanItem) => {
    const nodeId = item.uid;
    const nodeDef = nodeMap[item.node];
    const nodeType = nodeDef?.type || "custom_agent_node";
    if (nodeType === "user_question_node") {
      nodeLevel[nodeId] = 0;
      if (!nodesByLevel[0]) nodesByLevel[0] = [];
      nodesByLevel[0].push(nodeId);
    }
  });

  // Assign levels for non-final nodes
  let allAssigned = false;
  while (!allAssigned) {
    allAssigned = true;
    graphFlow.plan.forEach((item: PlanItem) => {
      const nodeId = item.uid;
      const nodeDef = nodeMap[item.node];
      const nodeType = nodeDef?.type || "custom_agent_node";
      if (nodeLevel[nodeId] !== undefined) return;
      if (nodeType === "final_answer_node") return;

      const predecessors = nodePredecessors[nodeId] || [];
      const allPredHaveLevels = predecessors.every((id) => nodeLevel[id] !== undefined);
      if (!allPredHaveLevels) {
        allAssigned = false;
        return;
      }

      let level: number;
      if (predecessors.length === 0) level = 1;
      else level = Math.max(...predecessors.map((id) => nodeLevel[id])) + 1;
      nodeLevel[nodeId] = level;
      if (!nodesByLevel[level]) nodesByLevel[level] = [];
      nodesByLevel[level].push(nodeId);
    });
  }

  // Final layer: final_answer_node
  graphFlow.plan.forEach((item: PlanItem) => {
    const nodeId = item.uid;
    const nodeDef = nodeMap[item.node];
    const nodeType = nodeDef?.type || "custom_agent_node";
    if (nodeType === "final_answer_node") {
      const levels = Object.keys(nodesByLevel).map(Number);
      const maxLevel = levels.length > 0 ? Math.max(...levels) : -1;
      const finalLevel = maxLevel + 1;
      nodeLevel[nodeId] = finalLevel;
      if (!nodesByLevel[finalLevel]) nodesByLevel[finalLevel] = [];
      nodesByLevel[finalLevel].push(nodeId);
    }
  });

  const nodes: LayoutNode[] = graphFlow.plan.map((item: PlanItem) => {
    const nodeDef = nodeMap[item.node] || null;
    const nodeType = nodeDef?.type || "custom_agent_node";
    const label = nodeDef?.name || item.meta?.display_name || "Node";
    const description = item.meta?.description || null;
    const level = nodeLevel[item.uid] ?? 0;
    return {
      id: item.uid,
      label,
      description,
      type: nodeType,
      level,
      elementDetails: nodeDef ? getElementDetails(nodeDef) : {},
      resolvedElements: getResolvedElements(graphFlow, nodeDef),
      nodeDefinition: nodeDef,
    };
  });

  const edges: LayoutEdge[] = [];
  graphFlow.plan.forEach((item: PlanItem) => {
    if (item.after) {
      const predecessors = Array.isArray(item.after) ? item.after : [item.after];
      predecessors.forEach((predId) => {
        edges.push({ source: predId, target: item.uid });
      });
    }
    if (item.branches) {
      Object.entries(item.branches).forEach(([branchKey, targetId]) => {
        edges.push({
          source: item.uid,
          target: targetId as string,
          isConditional: true,
          branchKey,
        });
      });
    }
  });

  return { nodes, edges };
}
