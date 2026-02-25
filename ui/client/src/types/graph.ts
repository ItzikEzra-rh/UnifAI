export interface BuildingBlock {
  id: string;
  type: string;
  label: string;
  color: string;
  description: string;
  workspaceData?: WorkspaceData;
}

export interface WorkspaceData {
  rid: string;
  name: string;
  category: string;
  type: string;
  config: any;
  version: number;
  created: string;
  updated: string;
  nested_refs: string[];
}

// ---------------------------------------------------------------------------
// Library-agnostic canvas types (no ReactFlow / JointJS dependency)
// ---------------------------------------------------------------------------

export interface CanvasNodeData {
  label: string;
  icon: React.ReactNode;
  color: string;
  style: string;
  description: string;
  workspaceData?: WorkspaceData;
  onDelete?: (id: string) => void;
  allBlocks?: BuildingBlock[];
  referencedConditions?: BuildingBlock[];
  onAttachCondition?: (nodeId: string, condition: BuildingBlock) => void;
  onRemoveCondition?: (nodeId: string, conditionRid: string) => void;
  isConnectionSource?: boolean;
  isConnectionTarget?: boolean;
}

export interface CanvasNode {
  id: string;
  position: { x: number; y: number };
  data: CanvasNodeData;
  selected?: boolean;
  width?: number;
  height?: number;
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  data?: {
    label?: string;
    isConditional?: boolean;
  };
}

export interface CurrentGraph {
  id: string;
  name: string;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  metadata: {
    created: Date;
    lastModified: Date;
    nodeCount: number;
    edgeCount: number;
  };
}

/** @deprecated Use CanvasNodeData instead */
export type CustomNodeData = CanvasNodeData;
