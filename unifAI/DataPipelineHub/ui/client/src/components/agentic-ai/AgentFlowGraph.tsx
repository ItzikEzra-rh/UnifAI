import React, { useCallback, useState, useEffect, useRef } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  NodeTypes,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
  NodeProps,
  Handle,
  useReactFlow 
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion } from 'framer-motion';
import { Plus, Activity, Database, FileText, Zap, Filter, GitBranch, MessageSquare, Bot, BookOpen, LucideIcon, Key } from 'lucide-react';
import { NodeData, GraphFlow, FlowObject } from './graphs/interfaces'
import { latestExampleGraphFlow } from './graphs/static-data/exampleGraphFlow'
import axios from '../../http/axiosAgentConfig'

// Custom node components
const AgentNode: React.FC<NodeProps<NodeData>> = ({ data, selected }) => {
  // Match the hex color code inside bg-[#...]
  const bgmatcher = data.style.match(/bg-\[#([0-9A-Fa-f]{6})\]/);
  const bgcolor = bgmatcher ? bgmatcher[1] : null;

  return (
    <>
      {/* Explicit top handle using ReactFlow's Handle component */}
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: `#${bgcolor}`, width: 10, height: 10 }}
      />
      
      <motion.div 
        className={`px-4 py-2 rounded-lg shadow-md ${data.style} flex items-center transition-all`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, scale: selected ? 1.05 : 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="mr-2">{data.icon}</div>
        <div>
          <div className="font-medium text-sm">{data.label}</div>
          {data.description && <div className={`text-xs ${data.style.includes("text-white") ? "text-gray-400" : "text-white"}`}>{data.description}</div>}
        </div>
      </motion.div>
      
      {/* Explicit bottom handle using ReactFlow's Handle component */}
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: `#${bgcolor}`, width: 10, height: 10 }}
      />
    </>
  );
};

const nodeTypes: NodeTypes = {
  agent: AgentNode,
};

// Function to generate a random icon
const getRandomIcon = (nodeType: string): React.ReactNode => {
  // Handle specific node types with consistent icons
  if (nodeType === 'user_question_node') {
    return <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">💬</div>;
  } else if (nodeType === 'final_answer_node') {
    return <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🤖</div>;
  }
  
  // For other node types, select from a predefined set of icons
  const icons: React.ReactNode[] = [
    <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🔍</div>,
    <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">📚</div>,
    <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🧠</div>,
    <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🔎</div>,
    <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🔧</div>,
    <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">✍️</div>,
  ];
  
  // Generate a deterministic index based on the node type
  const hash = nodeType.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return icons[hash % icons.length];
};

// Get node style based on node type
const getNodeStyle = (nodeType: string): string => {
  if (nodeType === 'user_question_node') {
    return 'bg-[#8A2BE2] text-white';
  } else if (nodeType === 'final_answer_node') {
    return 'bg-[#FF5722] text-white';
  } else {
    return 'bg-[#03DAC6] text-gray-800';
  }
};


// Function to generate edge color based on source node type
const getEdgeStyle = (sourceNodeType: string): { stroke: string; color: string } => {
  if (sourceNodeType === 'user_question_node') {
    return { stroke: '#8A2BE2', color: '#8A2BE2' };
  } else if (sourceNodeType === 'final_answer_node') {
    return { stroke: '#FF5722', color: '#FF5722' };
  } else {
    return { stroke: '#03DAC6', color: '#03DAC6' };
  }
};


// Function to parse the JSON graph flow into ReactFlow nodes and edges
const parseGraphFlow = (graphFlow: GraphFlow): { nodes: Node<NodeData>[]; edges: Edge[] } => {
  if (!graphFlow || !graphFlow.plan) {
    return { nodes: [], edges: [] };
  }

  // Create a map to store node types for edge styling
  const nodeTypeMap: Record<string, string> = {};
  
  // Create maps to build the layout
  const nodesByLevel: Record<number, string[]> = {}; // Level -> Node IDs
  const nodeLevel: Record<string, number> = {}; // Node ID -> Level
  const nodePredecessors: Record<string, string[]> = {}; // Node ID -> Predecessor IDs
  const nodeSuccessors: Record<string, string[]> = {}; // Node ID -> Successor IDs
  
  // First pass: Identify predecessors and successors
  graphFlow.plan.forEach(item => {
    const nodeId = item.uid;
    const nodeType = item.node?.type || 'custom_agent_node';
    nodeTypeMap[nodeId] = nodeType;
    
    if (item.after) {
      // Handle both string and array 'after' properties
      const predecessors = Array.isArray(item.after) ? item.after : [item.after];
      nodePredecessors[nodeId] = predecessors;
      
      // Record this node as a successor to each predecessor
      predecessors.forEach(predecessorId => {
        if (!nodeSuccessors[predecessorId]) {
          nodeSuccessors[predecessorId] = [];
        }
        nodeSuccessors[predecessorId].push(nodeId);
      });
    } else {
      // No predecessors, this is a root node
      nodePredecessors[nodeId] = [];
      nodeLevel[nodeId] = 0;
      if (!nodesByLevel[0]) {
        nodesByLevel[0] = [];
      }
      nodesByLevel[0].push(nodeId);
    }
  });
  
  // Second pass: Determine node levels
  let allNodesAssigned = false;
  while (!allNodesAssigned) {
    allNodesAssigned = true;
    graphFlow.plan.forEach(item => {
      const nodeId = item.uid;
      
      // Skip nodes that already have a level assigned
      if (nodeLevel[nodeId] !== undefined) {
        return;
      }
      
      const predecessors = nodePredecessors[nodeId] || [];
      
      // Check if all predecessors have levels assigned
      const allPredecessorsHaveLevels = predecessors.every(predId => 
        nodeLevel[predId] !== undefined
      );
      
      if (allPredecessorsHaveLevels) {
        // Find the maximum level among predecessors
        const maxPredLevel = Math.max(...predecessors.map(predId => nodeLevel[predId]));
        const level = maxPredLevel + 1;
        
        // Assign this node to the next level
        nodeLevel[nodeId] = level;
        if (!nodesByLevel[level]) {
          nodesByLevel[level] = [];
        }
        nodesByLevel[level].push(nodeId);
      } else {
        allNodesAssigned = false;
      }
    });
  }
  
  // Create nodes with the calculated positions
  const nodes: Node<NodeData>[] = graphFlow.plan.map(item => {
    const nodeId = item.uid;
    const nodeType = item.node?.type || 'custom_agent_node';
    const nodeLabel = item.meta?.display_name || item.node?._meta.display_name || "General Node";
    const nodeDescription = item.meta?.description || item.node?._meta.description || null;
    
    // Get level information
    const level = nodeLevel[nodeId];
    const nodesInSameLevel = nodesByLevel[level] || [];
    const indexInLevel = nodesInSameLevel.indexOf(nodeId);
    const totalInLevel = nodesInSameLevel.length;
    
    // Calculate position
    // Horizontal spacing increases with the number of nodes in the level
    const levelWidth = Math.max(totalInLevel * 300, 400);
    const xSpacing = levelWidth / totalInLevel;
    const xOffset = (xSpacing / 2) + (indexInLevel * xSpacing);
    const yOffset = level * 150;
    
    // Determine node style and icon
    const style = getNodeStyle(nodeType);
    const icon = getRandomIcon(nodeType);
    
    // Always set sourcePosition and targetPosition to ensure edges connect properly
    const sourcePosition = Position.Bottom;
    const targetPosition = Position.Top;
    
    return {
      id: nodeId,
      type: 'agent',
      data: {
        label: nodeLabel,
        description: nodeDescription,
        style: style,
        icon: icon
      },
      position: { x: xOffset, y: yOffset },
      sourcePosition,
      targetPosition
    };
  });
  
  // Create edges between nodes
  const edges: Edge[] = [];
  
  graphFlow.plan.forEach(item => {
    if (item.after) {
      // Handle both string and array 'after' properties
      const predecessors = Array.isArray(item.after) ? item.after : [item.after];
      
      predecessors.forEach(predecessorId => {
        const sourceNodeType = nodeTypeMap[predecessorId] || 'custom_agent_node';
        const edgeStyle = getEdgeStyle(sourceNodeType);
        
        edges.push({
          id: `${predecessorId}-to-${item.uid}`,
          source: predecessorId,
          target: item.uid,
          animated: true,
          type: 'default', // Simpler edge type for reliability
          style: { 
            stroke: edgeStyle.stroke, 
            strokeWidth: 2
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: edgeStyle.color,
            width: 10,
            height: 10
          },
          zIndex: 1000 // Ensure edges are on top
        });
      });
    }
  });

  return { nodes, edges };
};

// Function to convert graph flow JSON to flow object
const convertGraphFlowToFlowObject = (graphFlow: GraphFlow, index: number, graphId?: string): FlowObject => {
  if (!graphFlow) return null;

  // Extract metadata
  const name = graphFlow.display_name || `Flow ${index + 1}`;
  const description = graphFlow.display_description || 'No description available';

  // Generate a random icon for the flow
  const iconOptions: React.FC<{ className?: string }>[] = [Activity, Database, FileText, Zap, Filter, GitBranch, MessageSquare, BookOpen];
  const IconComponent = iconOptions[index % iconOptions.length];
  
  // Parse the graph flow into nodes and edges
  const { nodes, edges } = parseGraphFlow(graphFlow);
  
  return {
    id: graphId || `flow-${index}`,
    name,
    description,
    icon: <IconComponent className="h-4 w-4 mr-2" />,
    flow: {
      nodes,
      edges
    }
  };
};

// Fallback initial nodes and edges for demo
const initialNodes: Node<NodeData>[] = [
  {
    id: 'user-query',
    type: 'agent',
    data: { 
      label: 'User Query', 
      description: 'Input from user',
      style: 'bg-[#8A2BE2] text-white',
      icon: <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">💬</div>
    },
    position: { x: 250, y: 0 },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'llm-response',
    type: 'agent',
    data: { 
      label: 'LLM Response', 
      description: 'Output for user',
      style: 'bg-[#FF5722] text-white',
      icon: <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🤖</div>
    },
    position: { x: 250, y: 80 },
    targetPosition: Position.Top,
  },
];

const initialEdges: Edge[] = [
  {
    id: 'user-to-llm',
    source: 'user-query',
    target: 'llm-response',
    animated: true,
    style: { stroke: '#8A2BE2' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#8A2BE2',
    },
  },
];

type AgentFlowGraphProps = {
  selectedFlow: FlowObject | null;
  setSelectedFlow: (flow: FlowObject | null) => void;
};

export default function AgentFlowGraph({selectedFlow, setSelectedFlow}: AgentFlowGraphProps): React.ReactElement {
  // State for available graph flows
  const [graphFlows, setGraphFlows] = useState<FlowObject[]>([]);
  const [isInitial, setIsInitial] = useState<boolean>(true);
  const [nodes, setNodes, onNodesChange] = useNodesState<NodeData>(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const { fitView, zoomOut } = useReactFlow();
  const initializedRef = useRef(false);

  // Effect to load graph flows from API or mock data
  useEffect(() => {
    // For now, we'll use the example graph flow
    // const mockGraphFlows: GraphFlow[] = latestExampleGraphFlow.flatMap((plan) => Object.values(plan))

    const fetchGraphFlows = async () => {
      try {
        const response = await axios.get('/api/blueprints/available.blueprints.get');
        const planKeys: string[] = response.data.flatMap((plan) => Object.keys(plan));
        const mockGraphFlows: GraphFlow[] = response.data.flatMap((plan) => Object.values(plan));

        // Convert the mock graph flows to the format expected by the component
        const processedFlows = mockGraphFlows.map((flow, index) =>
          convertGraphFlowToFlowObject(flow, index, planKeys[index])
        );
        setGraphFlows(processedFlows);
        
        // Select the first flow by default
        if (processedFlows.length > 0) {
          setIsInitial(false);
          setSelectedFlow(processedFlows[0]);
          setNodes(processedFlows[0].flow.nodes);
          setEdges(processedFlows[0].flow.edges);
        }
      } catch (error) {
        console.error('Error fetching avaliable plans:', error);
      }
    };
    
    fetchGraphFlows();
  }, []);

  useEffect(() => {
    if (!initializedRef.current && nodes.length > 0 && edges.length > 0 && !isInitial) {
      initializedRef.current = true;
  
      // Slight delay to let the graph render
      setTimeout(() => {
        fitView({ padding: 0.2 });
        setTimeout(() => {
          zoomOut(); // mimic one click on Zoom Out
        }, 200);
      }, 100);
    }
  }, [nodes, edges]);

  const handleFlowSelect = (flow: FlowObject): void => {
    setSelectedFlow(flow);
    setNodes(flow.flow.nodes);
    setEdges(flow.flow.edges);
  };

  // Function to handle loading a new graph flow
  const handleLoadGraphFlow = (graphFlowJson: string): void => {
    try {
      const parsedFlow = JSON.parse(graphFlowJson) as GraphFlow;
      const newFlow = convertGraphFlowToFlowObject(parsedFlow, graphFlows.length);
      
      // Add the new flow to the list
      setGraphFlows(prev => [...prev, newFlow]);
      
      // Select the new flow
      setSelectedFlow(newFlow);
      setNodes(newFlow.flow.nodes);
      setEdges(newFlow.flow.edges);
    } catch (error) {
      console.error("Error parsing graph flow:", error);
    }
  };

  return (
    <Card className="bg-background-card shadow-card border-gray-800">
      <CardHeader className="py-4 px-6 flex flex-row justify-between items-center">
        <CardTitle className="text-lg font-heading">Agent Flow Visualization</CardTitle>
      </CardHeader>
      <CardContent className="p-0" style={{ height: "80vh" }}>
        <div className="flex h-full">
          {/* Sidebar for graph selection */}
          <div className="w-1/5 border-r border-gray-800 bg-background-dark overflow-y-auto">
            <div className="py-3 px-4 border-b border-gray-800 bg-background-surface">
              <h3 className="text-sm font-medium">Available Flows</h3>
            </div>
            <div className="py-2">
              {graphFlows.map((flow) => (
                <motion.div
                  key={flow.id}
                  className={`px-4 py-2 border-l-2 cursor-pointer ${
                    selectedFlow?.id === flow.id
                      ? 'border-[#8A2BE2] bg-[#8A2BE2] bg-opacity-10'
                      : 'border-transparent hover:bg-background-surface'
                  }`}
                  onClick={() => handleFlowSelect(flow)}
                  whileHover={{ x: 2 }}
                  transition={{ duration: 0.1 }}
                >
                  <div className="flex items-center">
                    {flow.icon}
                    <span className="text-sm font-medium">{flow.name}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{flow.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
          
          {/* Graph visualization */}
          <div className="flex-grow">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            elementsSelectable={true}
            nodesConnectable={true}
            nodesDraggable={true}
            edgesFocusable={true}
            connectionLineType="smoothstep"
            defaultEdgeOptions={{
              type: 'smoothstep',
              animated: true,
              style: { stroke: '#8A2BE2', strokeWidth: 3 },
              markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 20,
                height: 20,
                color: '#8A2BE2'
              }
            }}
            attributionPosition="bottom-right"
          >
            <Controls />
            <MiniMap />
            <Background color="#aaa" gap={16} />
          </ReactFlow>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}