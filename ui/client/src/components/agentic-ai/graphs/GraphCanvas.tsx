import React, { useState, useMemo } from "react";
import {
  ReactFlowProvider,
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  NodeTypes,
  EdgeTypes,
  MarkerType,
  ConnectionLineType,
  useViewport,
} from "reactflow";
import "reactflow/dist/style.css";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Link2, X } from "lucide-react";
import CustomNode from "./CustomNode";
import CustomEdge from "./CustomEdge";
import BidirectionalOffsetEdge from "./BidirectionalOffsetEdge";
import GraphHeader from "./GraphHeader";
import * as yaml from 'js-yaml';
import { useTheme } from "@/contexts/ThemeContext";
import { deriveThemeColors } from "@/lib/colorUtils";

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

const edgeTypes: EdgeTypes = {
  custom: CustomEdge,
  bidirectionalOffset: BidirectionalOffsetEdge,
};

/**
 * Detect bidirectional edge pairs (A->B and B->A) and transform them into
 * offset edges so they render as two visually separated paths.
 */
const processBidirectionalEdges = (edges: Edge[], bidiColor: string = "#10B981"): Edge[] => {
  const edgeMap = new Map<string, Edge[]>();
  const processedEdges: Edge[] = [];

  edges.forEach(edge => {
    const key1 = `${edge.source}-${edge.target}`;
    const key2 = `${edge.target}-${edge.source}`;
    const existingKey = edgeMap.has(key1) ? key1 : edgeMap.has(key2) ? key2 : key1;
    if (!edgeMap.has(existingKey)) {
      edgeMap.set(existingKey, []);
    }
    edgeMap.get(existingKey)!.push(edge);
  });

  edgeMap.forEach((edgeGroup) => {
    if (edgeGroup.length === 2) {
      const [edge1, edge2] = edgeGroup;

      const offsetEdge1: Edge = {
        ...edge1,
        type: 'bidirectionalOffset',
        data: {
          ...edge1.data,
          bidirectionalPair: true,
          offsetDirection: 'right',
          pairId: edge2.id,
        },
        style: { stroke: bidiColor, strokeWidth: 2.5 },
        markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: bidiColor },
      };

      const offsetEdge2: Edge = {
        ...edge2,
        type: 'bidirectionalOffset',
        data: {
          ...edge2.data,
          bidirectionalPair: true,
          offsetDirection: 'left',
          pairId: edge1.id,
        },
        style: { stroke: bidiColor, strokeWidth: 2.5 },
        markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: bidiColor },
      };

      processedEdges.push(offsetEdge1, offsetEdge2);
    } else if (edgeGroup.length === 1) {
      processedEdges.push(edgeGroup[0]);
    }
  });

  return processedEdges;
};

interface GraphCanvasProps {
  nodes: Node[];
  edges: Edge[];
  yamlFlow?: any;
  onNodesChange: (changes: any[]) => void;
  onEdgesChange: (changes: any[]) => void;
  onDrop: (event: React.DragEvent) => void;
  onDragOver: (event: React.DragEvent) => void;
  onClearGraph: () => void;
  onSaveGraph: () => void;
  onDeleteEdge?: (edgeId: string) => void;
  onBack?: () => void;
  onAttachCondition?: (nodeId: string, condition: any) => void;
  onRemoveCondition?: (nodeId: string, conditionRid: string) => void;
  isGraphValid?: boolean;
  onNodeClick?: (event: React.MouseEvent, node: Node) => void;
  onPaneClick?: () => void;
  pendingConnectionSource?: string | null;
  onCancelConnection?: () => void;
}

const ConnectionBanner: React.FC<{
  pendingConnectionSource: string;
  nodes: Node[];
  edgeColor: string;
  bidiEdgeColor: string;
  onCancelConnection?: () => void;
}> = ({ pendingConnectionSource, nodes, edgeColor, bidiEdgeColor, onCancelConnection }) => {
  const viewport = useViewport();
  const sourceNode = nodes.find(n => n.id === pendingConnectionSource);

  if (!sourceNode) return null;

  const nodeWidth = sourceNode.width || 200;
  const centerX = (sourceNode.position.x + nodeWidth / 2) * viewport.zoom + viewport.x;
  const topY = sourceNode.position.y * viewport.zoom + viewport.y;
  const sourceLabel = sourceNode.data?.label || pendingConnectionSource;

  return (
    <div
      className="absolute z-40 flex items-center gap-3 text-white px-4 py-2.5 rounded-xl shadow-xl backdrop-blur-md border whitespace-nowrap"
      style={{
        left: centerX,
        top: Math.max(topY - 56, 8),
        transform: 'translateX(-50%)',
        background: `linear-gradient(to right, ${edgeColor}F2, ${edgeColor}CC)`,
        borderColor: `${bidiEdgeColor}60`,
        pointerEvents: 'auto',
      }}
    >
      <div
        className="flex items-center justify-center w-7 h-7 rounded-full border"
        style={{ backgroundColor: `${edgeColor}30`, borderColor: `${bidiEdgeColor}40` }}
      >
        <Link2 className="w-3.5 h-3.5 animate-pulse" style={{ color: bidiEdgeColor }} />
      </div>
      <span className="text-sm font-medium">
        Select a target to connect{" "}
        <span className="font-semibold" style={{ color: bidiEdgeColor }}>
          {sourceLabel}
        </span>
      </span>
      <button
        onClick={onCancelConnection}
        className="ml-1 p-1 rounded-md text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
        title="Cancel (ESC)"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodes,
  edges,
  yamlFlow,
  onNodesChange,
  onEdgesChange,
  onDrop,
  onDragOver,
  onClearGraph,
  onSaveGraph,
  onDeleteEdge,
  onBack,
  isGraphValid = false,
  onNodeClick,
  onPaneClick,
  pendingConnectionSource = null,
  onCancelConnection,
}) => {
  const [showYamlDebug, setShowYamlDebug] = useState(false);
  const { primaryHex } = useTheme();

  const { primary: edgeColor, primaryLight: bidiEdgeColor, conditionEdge: condEdgeColor } = useMemo(
    () => deriveThemeColors(primaryHex),
    [primaryHex],
  );

  const processedEdges = useMemo(
    () => processBidirectionalEdges(edges, bidiEdgeColor),
    [edges, bidiEdgeColor],
  );

  // Re-theme ALL edges so they always reflect the current primary color,
  // regardless of what color was baked at creation time.
  const themedEdges = useMemo(() => processedEdges.map(edge => {
    const isConditional = edge.data?.isConditional;
    const isBidirectional = edge.type === 'bidirectionalOffset';

    if (isBidirectional) {
      return {
        ...edge,
        type: edge.type || 'custom',
        data: { ...edge.data, onDelete: onDeleteEdge },
      };
    }

    if (isConditional) {
      return {
        ...edge,
        type: edge.type || 'custom',
        style: { ...edge.style, stroke: condEdgeColor },
        markerEnd: { type: MarkerType.ArrowClosed, color: condEdgeColor },
        data: { ...edge.data, onDelete: onDeleteEdge },
      };
    }

    return {
      ...edge,
      type: edge.type || 'custom',
      style: { ...edge.style, stroke: edgeColor, strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: edgeColor },
      data: { ...edge.data, onDelete: onDeleteEdge },
    };
  }), [processedEdges, edgeColor, condEdgeColor, onDeleteEdge]);

  return (
    <div className="flex-1 relative">
      <Card className="bg-background-card shadow-card border-gray-800 h-full">
        <GraphHeader
          onClearGraph={onClearGraph}
          onSaveGraph={onSaveGraph}
          onBack={onBack}
          isGraphValid={isGraphValid}
        />
        <CardContent className="p-0 h-full relative">
          {showYamlDebug && yamlFlow && (
            <div className="absolute top-4 right-4 z-50 bg-gray-900 border border-gray-700 rounded-lg p-4 max-w-md max-h-96 overflow-auto">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-medium text-white">YAML Flow State</h3>
                <button
                  onClick={() => setShowYamlDebug(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>
              <pre className="text-xs text-gray-300 overflow-auto">
                {yaml.dump(yamlFlow, { indent: 2, lineWidth: -1 })}
              </pre>
            </div>
          )}

          <button
            onClick={() => setShowYamlDebug(!showYamlDebug)}
            className="absolute top-4 right-4 z-40 bg-gray-800 hover:bg-gray-700 text-white px-3 py-1 text-xs rounded border border-gray-600"
          >
            {showYamlDebug ? 'Hide' : 'Show'} YAML
          </button>

          <div className="h-full relative" style={{ height: "calc(100vh - 180px)" }}>
            <ReactFlowProvider>
              {pendingConnectionSource && (
                <ConnectionBanner
                  pendingConnectionSource={pendingConnectionSource}
                  nodes={nodes}
                  edgeColor={edgeColor}
                  bidiEdgeColor={bidiEdgeColor}
                  onCancelConnection={onCancelConnection}
                />
              )}

              <ReactFlow
                nodes={nodes}
                edges={themedEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                nodesConnectable={false}
                onDrop={onDrop}
                onDragOver={onDragOver}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                fitView
                defaultViewport={{ x: 0, y: 0, zoom: 0.33 }}
                connectionLineType={ConnectionLineType.SmoothStep}
                defaultEdgeOptions={{
                  type: "custom",
                  animated: true,
                  style: { stroke: edgeColor, strokeWidth: 2 },
                  markerEnd: {
                    type: MarkerType.ArrowClosed,
                    width: 20,
                    height: 20,
                    color: edgeColor,
                  },
                }}
              >
                <Background color="#aaa" gap={16} />
                <Controls />
              </ReactFlow>
            </ReactFlowProvider>

            {nodes.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="text-center">
                  <Plus className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="mt-2 text-sm font-medium text-gray-300">No nodes yet</h3>
                  <p className="mt-1 text-sm text-gray-400">Drag building blocks from the sidebar to get started</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GraphCanvas;
