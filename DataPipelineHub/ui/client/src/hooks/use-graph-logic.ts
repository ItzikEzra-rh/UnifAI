import { useState, useCallback, useEffect } from "react";
import {
  Node,
  Edge,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
} from "reactflow";
import { useToast } from "@/hooks/use-toast";
import { CurrentGraph, BuildingBlock } from "@/types/graph";
import { getCategoryDisplay } from "@/components/shared/helpers";
import axios from "../http/axiosAgentConfig";

const defaulYmlState = {
    nodes: [
      {
        rid: "user_question",
        name: "user_question",
        config: {
          name: "User Input",
          type: "user_question_node"
        }
      },
      {
        rid: "final_answer",
        name: "final_answer",
        config: {
          name: "Final Answer",
          type: "final_answer_node"
        }
      }
    ],
    plan: [
      {
        uid: "user_input",
        node: "user_question"
      },
      {
        uid: "finalize",
        node: "final_answer"
      }
    ]
}

export const useGraphLogic = () => {
  const { toast } = useToast();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [nodeId, setNodeId] = useState(1);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [buildingBlocksData, setBuildingBlocksData] = useState<BuildingBlock[]>(
    [],
  );
  const [allBlocksData, setAllBlocksData] = useState<BuildingBlock[]>([]);
  const [isLoadingBlocks, setIsLoadingBlocks] = useState(true);

  const [currentGraph, setCurrentGraph] = useState<CurrentGraph>({
    id: `graph-${Date.now()}`,
    name: "Untitled Graph",
    nodes: [],
    edges: [],
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      nodeCount: 0,
      edgeCount: 0,
    },
  });

  // YAML flow state management
  const [yamlFlow, setYamlFlow] = useState(defaulYmlState);

  // Hard-coded user ID - will be made flexible later
  const USER_ID = "alice";

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
        nested_refs: resource.nested_refs,
      },
    };
  };

  const deleteNode = useCallback(
    (nodeId: string) => {
      // Prevent deletion of required nodes
      if (nodeId === "user_input" || nodeId === "finalize") {
        toast({
          title: "❌ Cannot Delete Required Node",
          description: "User Input and Final Answer nodes are required and cannot be deleted",
          variant: "destructive",
        });
        return;
      }

      setNodes((currentNodes) => {
        const updatedNodes = currentNodes.filter((node) => node.id !== nodeId);

        setCurrentGraph((prev) => ({
          ...prev,
          nodes: updatedNodes,
          metadata: {
            ...prev.metadata,
            lastModified: new Date(),
            nodeCount: updatedNodes.length,
          },
        }));

        return updatedNodes;
      });

      setEdges((currentEdges) => {
        const updatedEdges = currentEdges.filter(
          (edge) => edge.source !== nodeId && edge.target !== nodeId,
        );

        // Update YAML flow to remove references and connections
        setYamlFlow(prevFlow => {
          const updatedNodes = prevFlow.nodes.filter(node => 
            !node.rid.includes(nodeId) && node.rid !== `$ref:${nodeId}`
          );

          const updatedPlan = prevFlow.plan
            .filter(step => step.uid !== nodeId)
            .map(step => {
              if (step.after === nodeId) {
                const { after, ...stepWithoutAfter } = step;
                return stepWithoutAfter;
              }
              return step;
            });

          return {
            ...prevFlow,
            nodes: updatedNodes,
            plan: updatedPlan
          };
        });

        setCurrentGraph((prev) => ({
          ...prev,
          edges: updatedEdges,
          metadata: {
            ...prev.metadata,
            lastModified: new Date(),
            edgeCount: updatedEdges.length,
          },
        }));

        return updatedEdges;
      });
    },
    [setNodes, setEdges, toast],
  );

  // Initialize canvas with default required nodes
  const initializeDefaultNodes = useCallback(() => {
    const userInputNode: Node = {
      id: "user_input",
      type: "custom",
      position: { x: 200, y: 100 },
      data: {
        label: "User Input",
        icon: getCategoryDisplay("nodes").icon,
        color: "#4A90E2",
        style: "bg-blue-800 text-white border",
        description: "User question input node",
        workspaceData: {
          rid: "user_question",
          name: "user_question",
          category: "nodes",
          type: "user_question_node",
          config: {
            name: "User Input",
            type: "user_question_node"
          },
          version: 1,
          created: new Date().toISOString(),
          updated: new Date().toISOString(),
          nested_refs: []
        },
        onDelete: deleteNode,
        allBlocks: allBlocksData,
      },
    };

    const finalizeNode: Node = {
      id: "finalize",
      type: "custom",
      position: { x: 200, y: 300 },
      data: {
        label: "Final Answer",
        icon: getCategoryDisplay("nodes").icon,
        color: "#50C878",
        style: "bg-green-800 text-white border",
        description: "Final answer output node",
        workspaceData: {
          rid: "final_answer",
          name: "final_answer",
          category: "nodes",
          type: "final_answer_node",
          config: {
            name: "Final Answer",
            type: "final_answer_node"
          },
          version: 1,
          created: new Date().toISOString(),
          updated: new Date().toISOString(),
          nested_refs: []
        },
        onDelete: deleteNode,
        allBlocks: allBlocksData,
      },
    };

    setNodes([userInputNode, finalizeNode]);
    setNodeId(3); // Start from 3 since we have 2 default nodes
  }, [allBlocksData, deleteNode]);

  const loadBuildingBlocks = useCallback(async () => {
    try {
      setIsLoadingBlocks(true);
      const response = await axios.get(
        `/api/resources/resources.list?userId=${USER_ID}`,
      );
      const allBlocks = response.data.resources.map(transformResourceToBlock);

      // Store all blocks for reference lookup
      setAllBlocksData(allBlocks);

      // Filter to show only blocks with category "nodes"
      const nodeBlocks = allBlocks.filter(
        (block) => block.workspaceData?.category === "nodes",
      );
      setBuildingBlocksData(nodeBlocks);
    } catch (error) {
      console.error("Error loading workspace resources:", error);
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
    initializeDefaultNodes();
  }, [loadBuildingBlocks]);


  const isConnectionFeasible = useCallback(
    async (connection: Connection): Promise<boolean> => {
      if (!connection.source || !connection.target) {
        toast({
          title: "❌ Connection Error",
          description: "Can't connect: Invalid connection parameters",
          variant: "destructive",
        });
        return false;
      }

      try {
        const response = await axios.post("/api/blueprints/check.connection", {
          sourceBlockId: connection.source,
          targetBlockId: connection.target,
        });

        if (!response.data.feasible) {
          toast({
            title: "❌ Connection Not Allowed",
            description: `Can't connect ${connection.source} to ${connection.target}: Connection not allowed by node configuration`,
            variant: "destructive",
          });
          return false;
        }

        return true;
      } catch (error) {
        console.error("Error checking connection feasibility:", error);
        toast({
          title: "❌ Connection Error",
          description: "Failed to validate connection",
          variant: "destructive",
        });
        return false;
      }
    },
    [toast],
  );

  const onConnect = useCallback(
    async (params: Connection) => {
      // Test if the connection is feasible
      const isFeasible = await isConnectionFeasible(params);
      if (!isFeasible) {
        console.log("Connection not feasible, rejecting edge creation");
        return;
      }

      const newEdge = addEdge(params, edges);
      setEdges(newEdge);

      // Update YAML flow with the new connection
      setYamlFlow(prevFlow => {
        const updatedPlan = prevFlow.plan.map(step => {
          if (step.uid === params.target) {
            return {
              ...step,
              after: params.source
            };
          }
          return step;
        });

        return {
          ...prevFlow,
          plan: updatedPlan
        };
      });

      setCurrentGraph((prev) => ({
        ...prev,
        edges: newEdge,
        metadata: {
          ...prev.metadata,
          lastModified: new Date(),
          edgeCount: newEdge.length,
        },
      }));
    },
    [setEdges, edges, isConnectionFeasible],
  );


  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const blockData = event.dataTransfer.getData("application/reactflow");

      if (blockData) {
        const block = JSON.parse(blockData);
        console.log(block);
        const position = {
          x: event.clientX - reactFlowBounds.left - 75,
          y: event.clientY - reactFlowBounds.top - 25,
        };

        const nodeUid = `${block.id}-${nodeId}`;
        const newNode: Node = {
          id: nodeUid,
          type: "custom",
          position,
          data: {
            label: block.label,
            icon: getCategoryDisplay(block.workspaceData?.category || "default")
              .icon,
            color: block.color,
            style: `bg-gray-800 text-white border`,
            description: `${block.description}`,
            workspaceData: block.workspaceData,
            onDelete: deleteNode,
            allBlocks: allBlocksData,
          },
        };

        const updatedNodes = [...nodes, newNode];
        setNodes(updatedNodes);
        setNodeId(nodeId + 1);

        // Update YAML flow with the new node
        setYamlFlow(prevFlow => {
          const newYamlNode = {
            rid: `$ref:${block.workspaceData?.rid || block.id}`,
            name: block.workspaceData?.name || block.label,
            config: block.workspaceData?.config || {}
          };

          const newPlanStep = {
            uid: nodeUid,
            node: block.workspaceData?.rid || block.id
          };

          return {
            ...prevFlow,
            nodes: [...prevFlow.nodes, newYamlNode],
            plan: [...prevFlow.plan, newPlanStep]
          };
        });

        setCurrentGraph((prev) => ({
          ...prev,
          nodes: updatedNodes,
          metadata: {
            ...prev.metadata,
            lastModified: new Date(),
            nodeCount: updatedNodes.length,
            edgeCount: edges.length,
          },
        }));
      }
    },
    [nodeId, setNodes, nodes, deleteNode, allBlocksData],
  );

  const handleNodesChange = useCallback(
    (changes: any[]) => {
      onNodesChange(changes);

      const selected = nodes
        .filter((node) => node.selected)
        .map((node) => node.id);
      setSelectedNodes(selected);
    },
    [onNodesChange, nodes],
  );

  const onDragStart = (event: React.DragEvent, block: BuildingBlock) => {
    const blockData = {
      id: block.id,
      type: block.type,
      label: block.label,
      description: block.description,
      color: block.color,
      workspaceData: block.workspaceData,
    };
    event.dataTransfer.setData(
      "application/reactflow",
      JSON.stringify(blockData),
    );
    event.dataTransfer.effectAllowed = "move";

    // Create a simpler drag preview
    const dragPreview = document.createElement("div");
    dragPreview.style.cssText = `
      position: absolute;
      top: -1000px;
      left: -1000px;
      padding: 8px 12px;
      background: ${block.color || "#6B7280"};
      color: white;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      white-space: nowrap;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      pointer-events: none;
      z-index: 1000;
    `;
    dragPreview.textContent = block.label;
    document.body.appendChild(dragPreview);

    event.dataTransfer.setDragImage(dragPreview, 50, 20);
    setTimeout(() => {
      if (document.body.contains(dragPreview)) {
        document.body.removeChild(dragPreview);
      }
    }, 0);
  };

  const clearGraph = () => {
    // Reset to default nodes instead of clearing completely
    initializeDefaultNodes();
    setEdges([]);

    // Reset YAML flow to default state
    setYamlFlow(defaulYmlState);

    setCurrentGraph((prev) => ({
      ...prev,
      nodes: [],
      edges: [],
      metadata: {
        ...prev.metadata,
        lastModified: new Date(),
        nodeCount: 2,
        edgeCount: 0,
      },
    }));
  };

  const saveGraph = useCallback(async () => {
    try {
      const blueprint = {
        display_name: currentGraph.name,
        display_description: `Graph with ${nodes.length} nodes and ${edges.length} edges`,
        plan: nodes.map((node) => {
          const nodeBlockType = node.id.split("-")[0];
          const blockData = buildingBlocksData.find(
            (block) => block.id === nodeBlockType,
          );
          const workspaceData = node.data.workspaceData;

          const incomingEdges = edges.filter((edge) => edge.target === node.id);
          const after = incomingEdges.map((edge) => edge.source);

          return {
            uid: node.id,
            node: {
              type:
                workspaceData?.type || blockData?.type || "custom_agent_node",
              category: workspaceData?.category,
              config: workspaceData?.config,
              _meta: {
                display_name: node.data.label,
                description: node.data.description,
                rid: workspaceData?.rid,
                version: workspaceData?.version,
              },
            },
            meta: {
              display_name: node.data.label,
              description: node.data.description,
              position: node.position,
            },
            after: after.length > 0 ? after : undefined,
          };
        }),
      };

      const response = await axios.post("/api/blueprints/blueprint.save", {
        blueprintRaw: JSON.stringify(blueprint),
      });

      if (response.data.status === "success") {
        toast({
          title: "✅ Graph Saved Successfully",
          description: `Graph "${currentGraph.name}" saved with ${nodes.length} nodes and ${edges.length} edges`,
          variant: "default",
        });

        // Update current graph with the saved blueprint ID
        setCurrentGraph((prev) => ({
          ...prev,
          id: response.data.blueprint_id,
          metadata: {
            ...prev.metadata,
            lastModified: new Date(),
            nodeCount: nodes.length,
            edgeCount: edges.length,
          },
        }));
      } else {
        throw new Error(response.data.error || "Unknown error occurred");
      }
    } catch (error) {
      console.error("Error saving graph:", error);
      toast({
        title: "❌ Error Saving Graph",
        description: "Failed to save graph to server",
        variant: "destructive",
      });
    }
  }, [currentGraph, nodes, edges, buildingBlocksData, toast]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Delete" && selectedNodes.length > 0) {
        event.preventDefault();
        selectedNodes.forEach((nodeId) => deleteNode(nodeId));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedNodes, deleteNode]);

  return {
    nodes,
    edges,
    currentGraph,
    buildingBlocksData,
    allBlocksData,
    isLoadingBlocks,
    yamlFlow,
    handleNodesChange,
    onEdgesChange,
    onConnect,
    onDrop,
    onDragOver,
    onDragStart,
    clearGraph,
    saveGraph,
  };
};