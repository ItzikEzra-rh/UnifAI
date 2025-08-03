import { useState, useCallback, useEffect } from "react";
import {
  Node,
  Edge,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
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
        type: "user_question_node",
      },
    },
    {
      rid: "final_answer",
      name: "final_answer",
      config: {
        name: "Final Answer",
        type: "final_answer_node",
      },
    },
  ],
  plan: [
    {
      uid: "user_input",
      node: "user_question",
    },
    {
      uid: "finalize",
      node: "final_answer",
    },
  ],
};

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
  const [conditionsData, setConditionsData] = useState<BuildingBlock[]>([]);
  const [isLoadingBlocks, setIsLoadingBlocks] = useState(true);

  // Conditional edge modal state
  const [conditionalEdgeModal, setConditionalEdgeModal] = useState({
    isOpen: false,
    sourceNodeId: "",
    targetNodeId: "",
    conditionType: "",
    existingBranches: [] as string[],
  });

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
          description:
            "User Input and Final Answer nodes are required and cannot be deleted",
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
        setYamlFlow((prevFlow) => {
          const updatedNodes = prevFlow.nodes.filter(
            (node) =>
              !node.rid.includes(nodeId) && node.rid !== `$ref:${nodeId}`,
          );

          const updatedPlan = prevFlow.plan
            .filter((step) => step.uid !== nodeId)
            .map((step) => {
              if (step.after === nodeId) {
                const { after, ...stepWithoutAfter } = step;
                return stepWithoutAfter;
              }
              return step;
            });

          return {
            nodes: prevFlow.nodes,
            conditions: prevFlow.conditions || [],
            plan: updatedPlan,
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
            type: "user_question_node",
          },
          version: 1,
          created: new Date().toISOString(),
          updated: new Date().toISOString(),
          nested_refs: [],
        },
        onDelete: deleteNode,
        allBlocks: allBlocksData,
        referencedConditions: [],
        onAttachCondition: attachConditionToNode,
        onRemoveCondition: removeConditionFromNode,
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
            type: "final_answer_node",
          },
          version: 1,
          created: new Date().toISOString(),
          updated: new Date().toISOString(),
          nested_refs: [],
        },
        onDelete: deleteNode,
        allBlocks: allBlocksData,
        referencedConditions: [],
        onAttachCondition: attachConditionToNode,
        onRemoveCondition: removeConditionFromNode,
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

      // Filter to show only blocks with category "conditions"
      const conditionBlocks = allBlocks.filter(
        (block) => block.workspaceData?.category === "conditions",
      );
      setConditionsData(conditionBlocks);
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
    async (params: Connection): Promise<boolean> => {
      // Commenting out for now to allow all connections
      // try {
      //   const response = await axios.post("/api/graph/connection.feasible", {
      //     source: params.source,
      //     target: params.target,
      //     yamlFlow,
      //   });
      //   return response.data.feasible;
      // } catch (error) {
      //   console.error("Error checking connection feasibility:", error);
      //   return false;
      // }
      return true; // Allow all connections for now
    },
    [yamlFlow],
  );

  const onConnect = useCallback(
    async (params: Connection) => {
      // Comment out connection feasibility check for now
      // if (isConnectionFeasible(params)) {

        // Check if source node has a condition attached
        const sourceNode = nodes.find(node => node.id === params.source);
        const hasCondition = sourceNode?.data?.referencedConditions && 
                           sourceNode.data.referencedConditions.length > 0;

        if (hasCondition) {
          // Get condition type and existing branches
          const condition = sourceNode.data.referencedConditions[0];
          const conditionType = condition.workspaceData?.type || condition.type;

          // Get existing edges from this source to determine existing branches
          const existingEdges = edges.filter(edge => edge.source === params.source);
          const existingBranches = existingEdges
            .map(edge => edge.data?.branch)
            .filter(Boolean);

          // Open conditional edge modal
          setConditionalEdgeModal({
            isOpen: true,
            sourceNodeId: params.source || "",
            targetNodeId: params.target || "",
            conditionType: conditionType,
            existingBranches: existingBranches,
          });

          return; // Don't create edge immediately, wait for modal confirmation
        }

        // Regular edge creation for nodes without conditions
        const newEdge = addEdge(params, edges);

        setEdges(newEdge);

        // Update YAML flow with the new connection
        setYamlFlow((prevFlow) => {
          const updatedPlan = prevFlow.plan.map((step) => {
            if (step.uid === params.target) {
              // Get existing after value
              const existingAfter = step.after;
              let newAfter;

              if (!existingAfter) {
                // No existing after, set as single value
                newAfter = params.source;
              } else if (Array.isArray(existingAfter)) {
                // Already an array, add new source if not already present
                if (!existingAfter.includes(params.source!)) {
                  newAfter = [...existingAfter, params.source!];
                } else {
                  newAfter = existingAfter;
                }
              } else {
                // Single value exists, convert to array
                if (existingAfter !== params.source) {
                  newAfter = [existingAfter, params.source!];
                } else {
                  newAfter = existingAfter;
                }
              }

              return {
                ...step,
                after: newAfter,
              };
            }
            return step;
          });

          return {
            nodes: prevFlow.nodes,
            conditions: prevFlow.conditions || [],
            plan: updatedPlan,
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
      // }
    },
    [setEdges, edges, nodes, setConditionalEdgeModal],
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

        const nodeUid = `${block.workspaceData?.name || block.label}-${block.workspaceData?.rid || block.id}-${nodeId}`;
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
            referencedConditions: [],
            onAttachCondition: attachConditionToNode,
            onRemoveCondition: removeConditionFromNode,
          },
        };

        const updatedNodes = [...nodes, newNode];
        setNodes(updatedNodes);
        setNodeId(nodeId + 1);

        // Update YAML flow with the new node
        setYamlFlow((prevFlow) => {
          const nodeRid = `$ref:${block.workspaceData?.rid || block.id}`;

          // Check if this node already exists in the nodes array
          const nodeExists = prevFlow.nodes.some(node => node.rid === nodeRid);

          const newYamlNode = {
            rid: nodeRid,
            name: block.workspaceData?.name || block.label,
            config: block.workspaceData?.config || {},
          };

          const newPlanStep = {
            uid: nodeUid,
            node: block.workspaceData?.rid || block.id,
          };

          // Add node to nodes section if it doesn't exist
          const updatedNodes = nodeExists ? prevFlow.nodes : [...prevFlow.nodes, newYamlNode];

          return {
            nodes: updatedNodes,
            conditions: prevFlow.conditions || [],
            plan: [...prevFlow.plan, newPlanStep],
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

    const attachConditionToNode = (nodeId: string, condition: any) => {
        // Check if node already has a condition attached
        const targetNode = nodes.find(node => node.id === nodeId);
        if (targetNode?.data?.referencedConditions && targetNode.data.referencedConditions.length > 0) {
            toast({
                title: "❌ Condition Limit Reached",
                description: "Each node can only have one condition attached. Remove the existing condition first.",
                variant: "destructive",
            });
            return;
        }

        setNodes((prevNodes) =>
            prevNodes.map((node) =>
                node.id === nodeId
                    ? {
                          ...node,
                          data: {
                              ...node.data,
                              referencedConditions: [condition], // Only allow one condition
                          },
                      }
                    : node,
            ),
        );

        // Update YAML flow to immediately set exit_condition
        setYamlFlow((prevFlow) => {
            const updatedPlan = prevFlow.plan.map((step) => {
                if (step.uid === nodeId) {
                    return {
                        ...step,
                        exit_condition: condition.workspaceData?.rid || condition.id,
                    };
                }
                return step;
            });

            return {
                nodes: prevFlow.nodes,
                conditions: prevFlow.conditions || [],
                plan: updatedPlan,
            };
        });
    };

    const removeConditionFromNode = (nodeId: string, conditionRid: string) => {
        setNodes((prevNodes) =>
            prevNodes.map((node) =>
                node.id === nodeId
                    ? {
                          ...node,
                          data: {
                              ...node.data,
                              referencedConditions: (
                                  node.data.referencedConditions || []
                              ).filter((condition) => 
                                  (condition.workspaceData?.rid || condition.id) !== conditionRid
                              ),
                          },
                      }
                    : node,
            ),
        );

        // Remove related edges
        setEdges((prevEdges) =>
            prevEdges.filter((edge) => edge.source !== nodeId),
        );

        // Update YAML flow to remove the condition and related connections
        setYamlFlow((prevFlow) => {
            // Remove condition from plan
            const updatedPlan = prevFlow.plan.map((step) => {
                if (step.uid === nodeId && step.exit_condition === conditionRid) {
                    const { exit_condition, branches, ...stepWithoutCondition } = step;
                    return stepWithoutCondition;
                }
                return step;
            });

            // Remove condition definition from conditions section (if exists)
            const updatedConditions = (prevFlow.conditions || []).filter(
                (cond) => cond.rid !== conditionRid,
            );

            return {
                nodes: prevFlow.nodes,
                conditions: updatedConditions.length > 0 ? updatedConditions : [],
                plan: updatedPlan,
            };
        });
    };

    const createConditionalEdge = (params: Connection, branchConfig: any) => {
        const edgeStyle = {
            strokeDasharray: "5,5",
            stroke: "#10b981",
        };

        const edgeId = `${params.source}-${params.target}-${branchConfig.branch || Date.now()}`;
        const newEdge = {
            id: edgeId,
            source: params.source!,
            target: params.target!,
            type: "default",
            style: edgeStyle,
            markerEnd: {
                type: MarkerType.ArrowClosed,
                color: "#10b981",
            },
            data: {
                ...branchConfig,
                isConditional: true,
            },
            label: branchConfig.branch || "",
        };

        setEdges((prevEdges) => [...prevEdges, newEdge]);

        // Update YAML flow for conditional connections
        setYamlFlow((prevFlow) => {
            const sourceNode = nodes.find(node => node.id === params.source);
            const condition = sourceNode?.data?.referencedConditions?.[0];

            const updatedPlan = prevFlow.plan.map((step) => {
                if (step.uid === params.source && condition) {
                    // Get existing branches or initialize empty object
                    const existingBranches = step.branches || {};

                    // Add new branch mapping based on condition type
                    let newBranches = { ...existingBranches };

                    if (branchConfig.conditionType === "router_direct") {
                        // For direct routing, map direct output to target step
                        newBranches[params.target!] = params.target!;
                    } else if (branchConfig.conditionType === "router_boolean") {
                        // For symbolic routing, map symbolic output to target step
                        // Convert boolean values to actual booleans for router_boolean
                        let branchKey = branchConfig.branch === "true" ? true : branchConfig.branch === "false" ? false : branchConfig.branch;
                        newBranches[branchKey] = params.target!;
                    }

                    return {
                        ...step,
                        exit_condition: condition.workspaceData?.rid || condition.id,
                        branches: newBranches,
                    };
                }
                return step;
            });

            // Add condition definition if not exists
            const conditionRid = condition?.workspaceData?.rid || condition?.id;
            const conditionExists = (prevFlow.conditions || []).some(
                (cond) => cond.rid === conditionRid
            );

            let updatedConditions = prevFlow.conditions || [];
            if (condition && !conditionExists) {
                updatedConditions = [
                    ...updatedConditions,
                    {
                        rid: conditionRid,
                        name: condition.workspaceData?.name || condition.label,
                        type: condition.workspaceData?.type,
                        config: condition.workspaceData?.config,
                    },
                ];
            }

            return {
                nodes: prevFlow.nodes,
                conditions: updatedConditions.length > 0 ? updatedConditions : [],
                plan: updatedPlan,
            };
        });

        setCurrentGraph((prev) => ({
            ...prev,
            edges: [...prev.edges, newEdge],
            metadata: {
                ...prev.metadata,
                lastModified: new Date(),
                edgeCount: prev.edges.length + 1,
            },
        }));
    };

    const handleConditionalEdgeConfirm = (branchConfig: any) => {
        const params = {
            source: conditionalEdgeModal.sourceNodeId,
            target: conditionalEdgeModal.targetNodeId,
        };

        createConditionalEdge(params, {
            ...branchConfig,
            conditionType: conditionalEdgeModal.conditionType,
        });

        setConditionalEdgeModal({
            isOpen: false,
            sourceNodeId: "",
            targetNodeId: "",
            conditionType: "",
            existingBranches: [],
        });
    };

    const handleConditionalEdgeCancel = () => {
        setConditionalEdgeModal({
            isOpen: false,
            sourceNodeId: "",
            targetNodeId: "",
            conditionType: "",
            existingBranches: [],
        });
    };

  return {
    nodes,
    edges,
    currentGraph,
    buildingBlocksData,
    conditionsData,
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
    attachConditionToNode,
    removeConditionFromNode,
    conditionalEdgeModal,
    handleConditionalEdgeConfirm,
    handleConditionalEdgeCancel,
  };
};