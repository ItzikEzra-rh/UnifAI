import React, { useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  NodeTypes,
  EdgeTypes,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from 'framer-motion';

// Custom node components
const AgentNode = ({ data, selected }: any) => {
  return (
    <motion.div 
      className={`px-4 py-2 rounded-lg shadow-md ${data.style} flex items-center transition-all`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1, scale: selected ? 1.05 : 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="mr-2">{data.icon}</div>
      <div>
        <div className="font-medium text-sm">{data.label}</div>
        {data.description && <div className="text-xs text-gray-400">{data.description}</div>}
      </div>
    </motion.div>
  );
};

const nodeTypes: NodeTypes = {
  agent: AgentNode,
};

// Initial nodes configuration
const initialNodes: Node[] = [
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
    id: 'query-parser',
    type: 'agent',
    data: { 
      label: 'Query Parser', 
      description: 'Analyzes user intent',
      style: 'bg-[#03DAC6] text-gray-800',
      icon: <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🔍</div>
    },
    position: { x: 250, y: 80 },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'context-retriever',
    type: 'agent',
    data: { 
      label: 'Context Retriever', 
      description: 'Fetches relevant data',
      style: 'bg-[#03DAC6] text-gray-800',
      icon: <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">📚</div>
    },
    position: { x: 100, y: 160 },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'planning-agent',
    type: 'agent',
    data: { 
      label: 'Planning Agent', 
      description: 'Creates execution plan',
      style: 'bg-[#03DAC6] text-gray-800',
      icon: <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🧠</div>
    },
    position: { x: 250, y: 160 },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'research-agent',
    type: 'agent',
    data: { 
      label: 'Research Agent', 
      description: 'Gathers information',
      style: 'bg-[#03DAC6] text-gray-800',
      icon: <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🔎</div>
    },
    position: { x: 400, y: 160 },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'tool-agent',
    type: 'agent',
    data: { 
      label: 'Tool Agent', 
      description: 'Uses external tools',
      style: 'bg-[#03DAC6] text-gray-800',
      icon: <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">🔧</div>
    },
    position: { x: 250, y: 240 },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'response-generator',
    type: 'agent',
    data: { 
      label: 'Response Generator', 
      description: 'Creates final answer',
      style: 'bg-[#03DAC6] text-gray-800',
      icon: <div className="w-6 h-6 rounded-full bg-white bg-opacity-30 flex items-center justify-center text-xs">✍️</div>
    },
    position: { x: 250, y: 320 },
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
    position: { x: 250, y: 400 },
    targetPosition: Position.Top,
  },
];

// Initial edges configuration
const initialEdges: Edge[] = [
  {
    id: 'user-to-parser',
    source: 'user-query',
    target: 'query-parser',
    animated: true,
    style: { stroke: '#8A2BE2' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#8A2BE2',
    },
  },
  {
    id: 'parser-to-context',
    source: 'query-parser',
    target: 'context-retriever',
    animated: true,
    style: { stroke: '#03DAC6' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#03DAC6',
    },
  },
  {
    id: 'parser-to-planning',
    source: 'query-parser',
    target: 'planning-agent',
    animated: true,
    style: { stroke: '#03DAC6' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#03DAC6',
    },
  },
  {
    id: 'parser-to-research',
    source: 'query-parser',
    target: 'research-agent',
    animated: true,
    style: { stroke: '#03DAC6' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#03DAC6',
    },
  },
  {
    id: 'context-to-tool',
    source: 'context-retriever',
    target: 'tool-agent',
    animated: true,
    style: { stroke: '#03DAC6' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#03DAC6',
    },
  },
  {
    id: 'planning-to-tool',
    source: 'planning-agent',
    target: 'tool-agent',
    animated: true,
    style: { stroke: '#03DAC6' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#03DAC6',
    },
  },
  {
    id: 'research-to-tool',
    source: 'research-agent',
    target: 'tool-agent',
    animated: true,
    style: { stroke: '#03DAC6' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#03DAC6',
    },
  },
  {
    id: 'tool-to-response',
    source: 'tool-agent',
    target: 'response-generator',
    animated: true,
    style: { stroke: '#03DAC6' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#03DAC6',
    },
  },
  {
    id: 'response-to-llm',
    source: 'response-generator',
    target: 'llm-response',
    animated: true,
    style: { stroke: '#FF5722' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#FF5722',
    },
  },
];

export default function AgentFlowGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <Card className="bg-background-card shadow-card border-gray-800">
      <CardHeader className="py-4 px-6">
        <CardTitle className="text-lg font-heading">Agent Flow Visualization</CardTitle>
      </CardHeader>
      <CardContent className="p-0" style={{ height: 500 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-right"
        >
          <Controls />
          <MiniMap />
          <Background color="#aaa" gap={16} />
        </ReactFlow>
      </CardContent>
    </Card>
  );
}