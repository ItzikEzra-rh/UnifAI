import React, { useState, useCallback, useEffect } from 'react';
import { ReactFlowProvider, ReactFlow, Node, Edge, addEdge, Connection, useNodesState, useEdgesState, Background, Controls, MiniMap, NodeTypes, MarkerType, Position, Handle, NodeProps, ConnectionLineType } from 'reactflow';
import 'reactflow/dist/style.css';
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { motion } from "framer-motion";
import { Plus, Bot, Settings, Trash2, Save, Play, X} from 'lucide-react';

interface CurrentGraph {
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

const CustomNode: React.FC<NodeProps> = ({ data, selected, id }) => {
  return (
    <>
      <Handle
        type="target"
        position={Position.Top}
        style={{ 
          background: data.color, 
          width: 10, 
          height: 10
        }}
      />
      
      <motion.div 
        className={`rounded-lg px-4 py-3 border-2 min-w-[150px] relative ${data.style} ${
          selected ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-gray-600'
        }`}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        {selected && (
          <button
            className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600 transition-colors"
            onClick={() => data.onDelete && data.onDelete(id)}
          >
            <X className="w-3 h-3" />
          </button>
        )}
        
        <div className="flex items-center gap-2 mb-1">
          {data.icon}
          <span className="font-medium text-sm">{data.label}</span>
        </div>
        {data.description && (
          <p className="text-xs text-gray-400">{data.description}</p>
        )}
      </motion.div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ 
          background: data.color, 
          width: 10, 
          height: 10
        }}
      />
    </>
  );
};

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

const buildingBlocksData = [
  {
    id: 'node1',
    type: 'custom',
    label: 'Node1',
    iconType: 'bot',
    color: '#8A2BE2',
    connectIn: 'node2',
    connectOut: 'node2'
  },
  {
    id: 'node2',
    type: 'custom',
    label: 'Node2',
    iconType: 'bot',
    color: '#00B0FF',
    connectIn: ['node1', 'node3'],
    connectOut: ['node1', 'node3']
  },
  {
    id: 'node3',
    type: 'custom',
    label: 'Node3',
    iconType: 'bot',
    color: '#FFB300',
    connectIn: ['node1'],
    connectOut: ['node1']
  },
];

// colors = #03DAC6, #FF5722, #00E676

const getIconComponent = (iconType: string) => {
  switch (iconType) {
    case 'bot':
      return <Bot className="w-4 h-4" />;
    case 'settings':
      return <Settings className="w-4 h-4" />;
    default:
      return <Bot className="w-4 h-4" />;
  }
};

export default function NewGraph() {
  const { toast } = useToast();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [nodeId, setNodeId] = useState(1);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  
  const [currentGraph, setCurrentGraph] = useState<CurrentGraph>({
    id: `graph-${Date.now()}`,
    name: 'Untitled Graph',
    nodes: [],
    edges: [],
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      nodeCount: 0,
      edgeCount: 0
    }
  });

  const isConnectionFeasible = useCallback((connection: Connection) => {
    console.log('Testing edge feasibility between:', connection.source, 'and', connection.target);
    
    // Check if source and target exist
    if (!connection.source || !connection.target) {
      toast({
        title: "❌ Connection Error",
        description: "Can't connect: Invalid connection parameters",
        variant: "destructive",
      });
      return false;
    }
    
    const getBlockType = (nodeId: string) => {
      return nodeId.split('-')[0];
    };
    
    const getBlockData = (blockType: string) => {
      return buildingBlocksData.find(block => block.id === blockType);
    };
    
    const sourceBlockType = getBlockType(connection.source!);
    const targetBlockType = getBlockType(connection.target!);
    
    const sourceBlockData = getBlockData(sourceBlockType);
    const targetBlockData = getBlockData(targetBlockType);
    
    if (!sourceBlockData || !targetBlockData) {
      toast({
        title: "❌ Connection Error",
        description: `Can't connect ${connection.source} to ${connection.target}: Unknown node type`,
        variant: "destructive",
      });
      return false;
    }
    
    // Check if source can connect out to target
    const sourceCanConnectOut = Array.isArray(sourceBlockData.connectOut) 
      ? sourceBlockData.connectOut.includes(targetBlockType)
      : sourceBlockData.connectOut === targetBlockType;
    
    // Check if target can accept connection from source
    const targetCanConnectIn = Array.isArray(targetBlockData.connectIn)
      ? targetBlockData.connectIn.includes(sourceBlockType)
      : targetBlockData.connectIn === sourceBlockType;
    
    if (!sourceCanConnectOut || !targetCanConnectIn) {
      toast({
        title: "❌ Connection Not Allowed",
        description: `Can't connect ${sourceBlockType} to ${targetBlockType}`,
        variant: "destructive",
      });
      return false;
    }
    
    return true;
  }, [toast]);

  const onConnect = useCallback(
    (params: Connection) => {
      // Test if the connection is feasible
      if (!isConnectionFeasible(params)) {
        console.log('Connection not feasible, rejecting edge creation');
        return;
      }
      
      const newEdge = addEdge(params, edges);
      setEdges(newEdge);
      
      setCurrentGraph(prev => ({
        ...prev,
        edges: newEdge,
        metadata: {
          ...prev.metadata,
          lastModified: new Date(),
          edgeCount: newEdge.length
        }
      }));
    },
    [setEdges, edges, isConnectionFeasible]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const blockData = event.dataTransfer.getData('application/reactflow');

      if (blockData) {
        const block = JSON.parse(blockData);
        const position = {
          x: event.clientX - reactFlowBounds.left - 75,
          y: event.clientY - reactFlowBounds.top - 25,
        };

        const newNode: Node = {
          id: `${block.id}-${nodeId}`,
          type: 'custom',
          position,
          data: {
            label: block.label,
            icon: getIconComponent(block.iconType),
            color: block.color,
            style: `bg-gray-800 text-white border`,
            description: `${block.label} component for your graph`,
            onDelete: deleteNode
          },
        };

        const updatedNodes = [...nodes, newNode];
        setNodes(updatedNodes);
        setNodeId(nodeId + 1);
        
        // Update current graph state
        setCurrentGraph(prev => ({
          ...prev,
          nodes: updatedNodes,
          metadata: {
            ...prev.metadata,
            lastModified: new Date(),
            nodeCount: updatedNodes.length
          }
        }));
      }
    },
    [nodeId, setNodes, nodes]
  );

  const deleteNode = useCallback((nodeId: string) => {
    setNodes(currentNodes => {
      const updatedNodes = currentNodes.filter(node => node.id !== nodeId);
      
      setCurrentGraph(prev => ({
        ...prev,
        nodes: updatedNodes,
        metadata: {
          ...prev.metadata,
          lastModified: new Date(),
          nodeCount: updatedNodes.length
        }
      }));
      
      return updatedNodes;
    });
    
    setEdges(currentEdges => {
      const updatedEdges = currentEdges.filter(edge => 
        edge.source !== nodeId && edge.target !== nodeId
      );
      
      setCurrentGraph(prev => ({
        ...prev,
        edges: updatedEdges,
        metadata: {
          ...prev.metadata,
          lastModified: new Date(),
          edgeCount: updatedEdges.length
        }
      }));
      
      return updatedEdges;
    });
  }, [setNodes, setEdges]);

  const handleNodesChange = useCallback((changes: any[]) => {
    onNodesChange(changes);
    
    const selected = nodes
      .filter(node => node.selected)
      .map(node => node.id);
    setSelectedNodes(selected);
  }, [onNodesChange, nodes]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.key === 'Delete') && selectedNodes.length > 0) {
        event.preventDefault();
        selectedNodes.forEach(nodeId => deleteNode(nodeId));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNodes, deleteNode]);

  const onDragStart = (event: React.DragEvent, block: any) => {
    const blockData = {
      id: block.id,
      type: block.type,
      label: block.label,
      iconType: block.iconType,
      color: block.color
    };
    event.dataTransfer.setData('application/reactflow', JSON.stringify(blockData));
    event.dataTransfer.effectAllowed = 'move';
  };


  const clearGraph = () => {
    setNodes([]);
    setEdges([]);
    setNodeId(1);
    
    setCurrentGraph(prev => ({
      ...prev,
      nodes: [],
      edges: [],
      metadata: {
        ...prev.metadata,
        lastModified: new Date(),
        nodeCount: 0,
        edgeCount: 0
      }
    }));
  };

  const saveGraph = () => {
    const graphToSave = {
      ...currentGraph,
      nodes,
      edges,
      metadata: {
        ...currentGraph.metadata,
        lastModified: new Date(),
        nodeCount: nodes.length,
        edgeCount: edges.length
      }
    };
    
    console.log('Saving current graph:', graphToSave);
    // Implement actual save functionality
    toast({
      title: "✅ Graph Saved Successfully",
      description: `Graph "${currentGraph.name}" saved with ${nodes.length} nodes and ${edges.length} edges`,
      variant: "default",
    });
  };


  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          title="New Graph Builder" 
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} 
        />

        <main className="flex-1 overflow-hidden p-4 bg-background-dark">
          <div className="flex h-full gap-4">
            {/* Main Graph Area */}
            <div className="flex-1">
              <Card className="bg-background-card shadow-card border-gray-800 h-full">
                <CardHeader className="py-3 px-6 border-b border-gray-800">
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-lg font-heading">Graph Canvas</CardTitle>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={clearGraph}
                        className="flex items-center"
                      >
                        <Trash2 className="w-4 h-4" />
                        Clear
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={saveGraph}
                        className="bg-primary hover:bg-opacity-80 flex items-center"
                      >
                        <Save className="w-4 h-4" />
                        Save
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0 h-full">
                  <div className="h-full" style={{ height: 'calc(100vh - 180px)' }}>
                    <ReactFlowProvider>
                      <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={handleNodesChange}
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
                        <MiniMap />
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

            <div className="w-80">
              <Card className="bg-background-card shadow-card border-gray-800 h-full">
                <CardHeader className="py-3 px-6 border-b border-gray-800">
                  <CardTitle className="text-lg font-heading">Nodes</CardTitle>
                  <p className="text-sm text-gray-400">Drag components to the canvas</p>
                </CardHeader>
                <CardContent className="p-4">
                  <div className="space-y-3">
                    {buildingBlocksData.map((block) => (
                      <div
                         key={block.id}
                         className="bg-gray-800 rounded-lg p-4 cursor-grab active:cursor-grabbing border border-gray-700 hover:border-gray-600 transition-colors"
                         draggable
                         onDragStart={(event: React.DragEvent) => onDragStart(event, block)}
                       >
                        <div className="flex items-center gap-3">
                          <div 
                            className="w-10 h-10 rounded-lg flex items-center justify-center text-white"
                            style={{ backgroundColor: block.color }}
                          >
                            {getIconComponent(block.iconType)}
                          </div>
                          <div>
                            <h3 className="font-medium text-white">{block.label}</h3>
                            <p className="text-xs text-gray-400">
                              Drag to add to graph
                            </p>
                          </div>
                        </div>
                       </div>
                    ))}
                  </div>
                  
                  {/* Instructions */}
                  <div className="mt-6 p-4 bg-gray-900 rounded-lg border border-gray-700">
                    <h4 className="font-medium text-white mb-2">How to use:</h4>
                    <ul className="text-sm text-gray-400 space-y-1">
                      <li>• Drag blocks to the canvas</li>
                      <li>• Connect nodes by dragging from handles</li>
                      <li>• Click nodes to select them</li>
                      <li>• Press Delete button on keyboard/X button to remove selected nodes</li>
                      <li>• Use controls to zoom and pan</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
} 