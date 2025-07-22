import { Node, Edge } from 'reactflow';

export interface CurrentGraph {
  id: string;
  name: string;
  nodes: Node[];
  edges: Edge[];
  metadata: {
    created: Date;
    lastModified: Date;
    nodeCount: number;
    edgeCount: number;
  };
}

export interface BuildingBlock {
  id: string;
  type: string;
  label: string;
  iconType: string;
  color: string;
  connectIn: string | string[];
  connectOut: string | string[];
}

export interface CustomNodeData {
  label: string;
  icon: React.ReactNode;
  color: string;
  style: string;
  description: string;
  onDelete?: (id: string) => void;
} 