import React from 'react';
import { ReactFlowProvider, ReactFlow, Node, Edge, Connection, Background, Controls, NodeTypes, MarkerType, ConnectionLineType } from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent } from "@/components/ui/card";
import { Plus } from 'lucide-react';
import CustomNode from './CustomNode';
import GraphHeader from './GraphHeader';

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

interface GraphCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: (changes: any[]) => void;
  onEdgesChange: (changes: any[]) => void;
  onConnect: (params: Connection) => void;
  onDrop: (event: React.DragEvent) => void;
  onDragOver: (event: React.DragEvent) => void;
  onClearGraph: () => void;
  onSaveGraph: () => void;
}

const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onDrop,
  onDragOver,
  onClearGraph,
  onSaveGraph
}) => {
  return (
    <div className="flex-1">
      <Card className="bg-background-card shadow-card border-gray-800 h-full">
        <GraphHeader onClearGraph={onClearGraph} onSaveGraph={onSaveGraph} />
        <CardContent className="p-0 h-full">
          <div className="h-full" style={{ height: 'calc(100vh - 180px)' }}>
            <ReactFlowProvider>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onDrop={onDrop}
                onDragOver={onDragOver}
                nodeTypes={nodeTypes}
                fitView
                connectionLineType={ConnectionLineType.SmoothStep}
                defaultEdgeOptions={{
                  type: 'smoothstep',
                  animated: true,
                  style: { stroke: '#8A2BE2', strokeWidth: 2 },
                  markerEnd: {
                    type: MarkerType.ArrowClosed,
                    width: 20,
                    height: 20,
                    color: '#8A2BE2'
                  }
                }}
              >
                <Background color="#aaa" gap={16} />
                <Controls />
              </ReactFlow>
            </ReactFlowProvider>
            
            {/* Drop zone overlay when empty */}
            {nodes.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="text-center text-gray-500">
                  <Plus className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">Drag nodes and edges here to create your graph</p>
                  <p className="text-sm">Start by dragging components from the right panel</p>
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