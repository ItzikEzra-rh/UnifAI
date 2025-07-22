import { useState, useCallback, useEffect } from 'react';
import { Node, Edge, Connection, addEdge, useNodesState, useEdgesState } from 'reactflow';
import { useToast } from "@/hooks/use-toast";
import { CurrentGraph, BuildingBlock } from '@/types/graph';
import { buildingBlocksData, getIconComponent } from '@/workspace/nodeData';

export const useGraphLogic = () => {
  const { toast } = useToast();
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
    
    // Helper function to extract the block type from node id
    const getBlockType = (nodeId: string) => {
      // Node IDs are in format "node1-1", "node2-2", etc.
      return nodeId.split('-')[0];
    };
    
    // Helper function to get block data by type
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
        description: `Can't connect ${sourceBlockType} to ${targetBlockType}: Connection not allowed by node configuration`,
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
    [nodeId, setNodes, nodes, deleteNode]
  );

  const handleNodesChange = useCallback((changes: any[]) => {
    onNodesChange(changes);
    
    const selected = nodes
      .filter(node => node.selected)
      .map(node => node.id);
    setSelectedNodes(selected);
  }, [onNodesChange, nodes]);

  const onDragStart = (event: React.DragEvent, block: BuildingBlock) => {
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

  // Handle keyboard events for deletion
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

  return {
    nodes,
    edges,
    currentGraph,
    handleNodesChange,
    onEdgesChange,
    onConnect,
    onDrop,
    onDragOver,
    onDragStart,
    clearGraph,
    saveGraph
  };
}; 