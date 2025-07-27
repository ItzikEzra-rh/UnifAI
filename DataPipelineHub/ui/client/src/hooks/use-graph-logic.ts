import { useState, useCallback, useEffect } from 'react';
import { Node, Edge, Connection, addEdge, useNodesState, useEdgesState } from 'reactflow';
import { useToast } from "@/hooks/use-toast";
import { CurrentGraph, BuildingBlock } from '@/types/graph';
import { getCategoryDisplay } from '@/components/shared/helpers';
import axios from '../http/axiosAgentConfig';

export const useGraphLogic = () => {
  const { toast } = useToast();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [nodeId, setNodeId] = useState(1);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [buildingBlocksData, setBuildingBlocksData] = useState<BuildingBlock[]>([]);
  const [isLoadingBlocks, setIsLoadingBlocks] = useState(true);
  
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

  // Hard-coded user ID - will be made flexible later
  const USER_ID = 'alice';

  const transformResourceToBlock = (resource: any): BuildingBlock => {
    const display = getCategoryDisplay(resource.category);
    
    return {
      id: resource.rid,
      type: resource.type,
      label: resource.name,
      color: display.color,
      description: `${resource.category}/${resource.type} - ${resource.name}`,
      workspaceData: {
        rid: resource.rid,
        name: resource.name,
        category: resource.category,
        type: resource.type,
        config: resource.cfg_dict,
        version: resource.version,
        created: resource.created,
        updated: resource.updated,
        nested_refs: resource.nested_refs
      }
    };
  };

  const loadBuildingBlocks = useCallback(async () => {
    try {
      setIsLoadingBlocks(true);
      const response = await axios.get(`/api/resources/resources.list?userId=${USER_ID}`);
      // Transform workspace resources to BuildingBlock format
      const buildingBlocks = response.data.resources.map(transformResourceToBlock);
      setBuildingBlocksData(buildingBlocks);
    } catch (error) {
      console.error('Error loading workspace resources:', error);
      toast({
        title: "❌ Error Loading Resources",
        description: "Failed to load workspace resources from server",
        variant: "destructive",
      });
    } finally {
      setIsLoadingBlocks(false);
    }
  }, [toast]);

  useEffect(() => {
    loadBuildingBlocks();
  }, [loadBuildingBlocks]);

  const isConnectionFeasible = useCallback(async (connection: Connection): Promise<boolean> => {
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
    
    const sourceBlockType = getBlockType(connection.source!);
    const targetBlockType = getBlockType(connection.target!);

    try {
      const response = await axios.post('/api/blueprints/check.connection', {
        sourceBlockId: sourceBlockType,
        targetBlockId: targetBlockType
      });

      if (!response.data.feasible) {
        toast({
          title: "❌ Connection Not Allowed",
          description: `Can't connect ${sourceBlockType} to ${targetBlockType}: Connection not allowed by node configuration`,
          variant: "destructive",
        });
        return false;
      }

      return true;
    } catch (error) {
      console.error('Error checking connection feasibility:', error);
      toast({
        title: "❌ Connection Error",
        description: "Failed to validate connection",
        variant: "destructive",
      });
      return false;
    }
  }, [toast]);

  const onConnect = useCallback(
    async (params: Connection) => {
      // Test if the connection is feasible
      const isFeasible = await isConnectionFeasible(params);
      if (!isFeasible) {
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
        console.log(block)
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
            icon: getCategoryDisplay(block.workspaceData?.category || 'default').icon,
            color: block.color,
            style: `bg-gray-800 text-white border`,
            description: `${block.description}`,
            workspaceData: block.workspaceData,
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
      description: block.description,
      color: block.color,
      workspaceData: block.workspaceData
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

  const saveGraph = useCallback(async () => {
    try {
      const blueprint = {
        display_name: currentGraph.name,
        display_description: `Graph with ${nodes.length} nodes and ${edges.length} edges`,
        plan: nodes.map(node => {
          const nodeBlockType = node.id.split('-')[0];
          const blockData = buildingBlocksData.find(block => block.id === nodeBlockType);
          const workspaceData = node.data.workspaceData;
          
          const incomingEdges = edges.filter(edge => edge.target === node.id);
          const after = incomingEdges.map(edge => edge.source);
          
          return {
            uid: node.id,
            node: {
              type: workspaceData?.type || blockData?.type || 'custom_agent_node',
              category: workspaceData?.category,
              config: workspaceData?.config,
              _meta: {
                display_name: node.data.label,
                description: node.data.description,
                rid: workspaceData?.rid,
                version: workspaceData?.version
              }
            },
            meta: {
              display_name: node.data.label,
              description: node.data.description,
              position: node.position
            },
            after: after.length > 0 ? after : undefined
          };
        })
      };

      const response = await axios.post('/api/blueprints/blueprint.save', {
        blueprintRaw: JSON.stringify(blueprint)
      });

      if (response.data.status === 'success') {
        toast({
          title: "✅ Graph Saved Successfully",
          description: `Graph "${currentGraph.name}" saved with ${nodes.length} nodes and ${edges.length} edges`,
          variant: "default",
        });
        
        // Update current graph with the saved blueprint ID
        setCurrentGraph(prev => ({
          ...prev,
          id: response.data.blueprint_id,
          metadata: {
            ...prev.metadata,
            lastModified: new Date(),
            nodeCount: nodes.length,
            edgeCount: edges.length
          }
        }));
      } else {
        throw new Error(response.data.error || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Error saving graph:', error);
      toast({
        title: "❌ Error Saving Graph",
        description: "Failed to save graph to server",
        variant: "destructive",
      });
    }
  }, [currentGraph, nodes, edges, buildingBlocksData, toast]);

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
    buildingBlocksData,
    isLoadingBlocks,
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