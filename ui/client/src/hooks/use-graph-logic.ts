import { useState, useCallback, useEffect, useRef, useMemo } from "react";
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
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { deriveThemeColors } from "@/lib/colorUtils";
import axios from "../http/axiosAgentConfig";
import * as yaml from "js-yaml";
import { saveBlueprint } from "@/api/blueprints";

interface YamlFlowNode {
  rid: string;
  name: string;
  type?: string;
  config?: any;
}

interface YamlFlowPlanStep {
  uid: string;
  node: string;
  after?: string | string[] | null;
  branches?: any;
  exit_condition?: string;
}

interface YamlFlowCondition {
  rid: string;
  name: string;
  type?: string;
  config?: any;
}

interface YamlFlowState {
  name?: string;
  description?: string;
  nodes: YamlFlowNode[];
  plan: YamlFlowPlanStep[];
  conditions?: YamlFlowCondition[];
}

const defaulYmlState: YamlFlowState = {
  nodes: [
    {
      rid: "user_question",
      name: "User Question Node",
      type: "user_question_node",
      config: {
        type: "user_question_node",
      },
    },
    {
      rid: "final_answer",
      name: "Final Answer Node",
      type: "final_answer_node",
      config: {
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

export interface SavedBlueprintInfo {
  blueprintId: string;
  name: string;
  description: string;
}

interface UseGraphLogicOptions {
  /** Callback to execute after a successful save (e.g., navigate back to workflow list) */
  onSaveComplete?: (savedBlueprint?: SavedBlueprintInfo) => void;
}

export const useGraphLogic = (options: UseGraphLogicOptions = {}) => {
  const { onSaveComplete } = options;
  const { toast } = useToast();
  const { primaryHex } = useTheme();
  const themeColors = useMemo(() => deriveThemeColors(primaryHex), [primaryHex]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [nodeId, setNodeId] = useState(1);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);
  const [buildingBlocksData, setBuildingBlocksData] = useState<BuildingBlock[]>(
    [],
  );
  const [orchestratorsData, setOrchestratorsData] = useState<BuildingBlock[]>(
    [],
  );
  const [allBlocksData, setAllBlocksData] = useState<BuildingBlock[]>([]);
  const [conditionsData, setConditionsData] = useState<BuildingBlock[]>([]);
  const [isLoadingBlocks, setIsLoadingBlocks] = useState(true);

  // Click-to-connect state
  const [pendingConnectionSource, setPendingConnectionSource] = useState<string | null>(null);

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
  const [yamlFlow, setYamlFlow] = useState<YamlFlowState>(defaulYmlState);

  // Graph validation state
  const [isGraphValid, setIsGraphValid] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [fixSuggestions, setFixSuggestions] = useState<any[]>([]);
  const [isValidating, setIsValidating] = useState(false);

  // Save modal state
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Drag state to track what type of item is being dragged
  const [isDraggingCondition, setIsDraggingCondition] = useState(false);

  const { user } = useAuth();
  const USER_ID = user?.username || "default";

  // Stable refs for callbacks embedded in node data (avoids stale closures)
  const deleteNodeRef = useRef<(id: string) => void>(() => {});
  const attachConditionRef = useRef<(nodeId: string, condition: any) => void>(() => {});
  const removeConditionRef = useRef<(nodeId: string, conditionRid: string) => void>(() => {});
  const allBlocksRef = useRef<BuildingBlock[]>([]);

  // Stable callback wrappers that delegate to the latest ref
  const stableDeleteNode = useCallback((id: string) => deleteNodeRef.current(id), []);
  const stableAttachCondition = useCallback((nodeId: string, condition: any) => attachConditionRef.current(nodeId, condition), []);
  const stableRemoveCondition = useCallback((nodeId: string, rid: string) => removeConditionRef.current(nodeId, rid), []);

  // Validate graph using the validation API
  const validateGraph = useCallback(async () => {
    if (nodes.length <= 2) {
      // Don't validate empty or minimal graphs (just default nodes)
      setIsGraphValid(false);
      setValidationResult(null);
      setFixSuggestions([]);
      return;
    }

    try {
      setIsValidating(true);

      // Convert YAML flow to YAML string using js-yaml library
      const yamlFlowForValidation = {
        name: yamlFlow.name || "Untitled blueprint",
        description: yamlFlow.description || "default",
        conditions: yamlFlow.conditions || [],
        nodes: yamlFlow.nodes || [],
        plan: yamlFlow.plan || [],
      };

      const yamlString = yaml.dump(yamlFlowForValidation, {
        indent: 2,
        lineWidth: -1,
        noRefs: true,
        sortKeys: false,
      });

      const response = await axios.post(
        "/graph/validation/all.validate",
        yamlString,
        {
          headers: {
            "Content-Type": "text/plain",
          },
        },
      );

      const { validation_result, fix_suggestions } = response.data;

      setValidationResult(validation_result);
      setFixSuggestions(fix_suggestions || []);
      setIsGraphValid(validation_result?.is_valid || false);
    } catch (error) {
      console.error("Error validating graph:", error);
      setIsGraphValid(false);
      setValidationResult(null);
      setFixSuggestions([]);

      // Silent error - validation panel will show the status
      console.error("Validation failed:", error);
    } finally {
      setIsValidating(false);
    }
  }, [yamlFlow, nodes.length]);

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
  deleteNodeRef.current = deleteNode;

  const deleteEdge = useCallback(
    (edgeId: string) => {
      setEdges((currentEdges) => {
        const edgeToDelete = currentEdges.find((edge) => edge.id === edgeId);
        if (!edgeToDelete) return currentEdges;

        // Check for a reverse edge (bidirectional pair: A→B and B→A)
        const reverseEdge = currentEdges.find(
          (edge) =>
            edge.id !== edgeId &&
            edge.source === edgeToDelete.target &&
            edge.target === edgeToDelete.source,
        );

        const edgeIdsToRemove = new Set([edgeId]);
        if (reverseEdge) {
          edgeIdsToRemove.add(reverseEdge.id);
        }

        const edgesToRemove = [edgeToDelete, ...(reverseEdge ? [reverseEdge] : [])];
        const updatedEdges = currentEdges.filter((edge) => !edgeIdsToRemove.has(edge.id));

        // Update YAML flow to remove connections for all deleted edges
        setYamlFlow((prevFlow) => {
          let updatedPlan = [...prevFlow.plan];

          for (const removedEdge of edgesToRemove) {
            updatedPlan = updatedPlan.map((step) => {
              if (step.uid === removedEdge.target) {
                if (step.after) {
                  if (Array.isArray(step.after)) {
                    const updatedAfter = step.after.filter(
                      (afterId) => afterId !== removedEdge.source,
                    );
                    if (updatedAfter.length === 0) {
                      const { after, ...stepWithoutAfter } = step;
                      return stepWithoutAfter;
                    } else if (updatedAfter.length === 1) {
                      return { ...step, after: updatedAfter[0] };
                    } else {
                      return { ...step, after: updatedAfter };
                    }
                  } else if (step.after === removedEdge.source) {
                    const { after, ...stepWithoutAfter } = step;
                    return stepWithoutAfter;
                  }
                }

                if (step.branches) {
                  const updatedBranches = { ...step.branches };
                  Object.keys(updatedBranches).forEach((branchKey) => {
                    if (updatedBranches[branchKey] === removedEdge.target) {
                      delete updatedBranches[branchKey];
                    }
                  });

                  if (Object.keys(updatedBranches).length === 0) {
                    const { branches, ...stepWithoutBranches } = step;
                    return stepWithoutBranches;
                  } else {
                    return { ...step, branches: updatedBranches };
                  }
                }
              }
              return step;
            });
          }

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
    [setEdges],
  );

  const attachConditionToNode = (nodeId: string, condition: any) => {
    // Check if node already has a condition attached
    const targetNode = nodes.find((node) => node.id === nodeId);
    if (
      targetNode?.data?.referencedConditions &&
      targetNode.data.referencedConditions.length > 0
    ) {
      toast({
        title: "❌ Condition Limit Reached",
        description:
          "Each node can only have one condition attached. Remove the existing condition first.",
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

    // Update YAML flow to immediately set exit_condition and add condition definition
    setYamlFlow((prevFlow) => {
      const conditionRid = condition.workspaceData?.rid || condition.id;
      
      // Update plan with exit_condition
      const updatedPlan = prevFlow.plan.map((step) => {
        if (step.uid === nodeId) {
          return {
            ...step,
            exit_condition: conditionRid,
          };
        }
        return step;
      });

      // Add condition definition to conditions section if not exists
      const conditionExists = (prevFlow.conditions || []).some(
        (cond: any) => cond.rid === `$ref:${conditionRid}`,
      );

      let updatedConditions = prevFlow.conditions || [];
      if (!conditionExists) {
        updatedConditions = [
          ...updatedConditions,
          {
            rid: `$ref:${conditionRid}`,
            name: condition.workspaceData?.name || condition.label,
            type: condition.workspaceData?.type,
            config: condition.workspaceData?.config,
          },
        ];
      }

      return {
        ...prevFlow,
        conditions: updatedConditions,
        plan: updatedPlan,
      };
    });
  };

  attachConditionRef.current = attachConditionToNode;

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
                ).filter(
                  (condition: any) =>
                    (condition.workspaceData?.rid || condition.id) !==
                    conditionRid,
                ),
              },
            }
          : node,
      ),
    );

    // Remove related edges
    setEdges((prevEdges) => prevEdges.filter((edge) => edge.source !== nodeId));

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
        (cond: any) => cond.rid !== `$ref:${conditionRid}`,
      );

      return {
        ...prevFlow,
        conditions: updatedConditions.length > 0 ? updatedConditions : [],
        plan: updatedPlan,
      };
    });
  };

  removeConditionRef.current = removeConditionFromNode;

  // Keep allBlocksRef in sync
  allBlocksRef.current = allBlocksData;

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
        onDelete: stableDeleteNode,
        allBlocks: allBlocksRef.current,
        referencedConditions: [],
        onAttachCondition: stableAttachCondition,
        onRemoveCondition: stableRemoveCondition,
      },
    };

    const finalizeNode: Node = {
      id: "finalize",
      type: "custom",
      position: { x: 200, y: 900 },
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
        onDelete: stableDeleteNode,
        allBlocks: allBlocksRef.current,
        referencedConditions: [],
        onAttachCondition: stableAttachCondition,
        onRemoveCondition: stableRemoveCondition,
      },
    };

    setNodes([userInputNode, finalizeNode]);
    setNodeId(3);
  }, [stableDeleteNode, stableAttachCondition, stableRemoveCondition]);

  const loadBuildingBlocks = useCallback(async () => {
    try {
      setIsLoadingBlocks(true);
      const response = await axios.get(
        `/resources/resources.list?userId=${USER_ID}`,
      );
      const allBlocks = response.data.resources.map(transformResourceToBlock);

      setAllBlocksData(allBlocks);

      // Orchestrators are nodes with type "orchestrator_node"
      const orchestratorBlocks = allBlocks
        .filter(
          (block: BuildingBlock) =>
            block.workspaceData?.category === "nodes" &&
            block.workspaceData?.type === "orchestrator_node",
        )
        .sort((a: BuildingBlock, b: BuildingBlock) =>
          a.label.localeCompare(b.label),
        );
      setOrchestratorsData(orchestratorBlocks);

      // Agents are all other nodes (not orchestrators)
      const nodeBlocks = allBlocks
        .filter(
          (block: BuildingBlock) =>
            block.workspaceData?.category === "nodes" &&
            block.workspaceData?.type !== "orchestrator_node",
        )
        .sort((a: BuildingBlock, b: BuildingBlock) =>
          a.label.localeCompare(b.label),
        );
      setBuildingBlocksData(nodeBlocks);

      const conditionBlocks = allBlocks
        .filter(
          (block: BuildingBlock) =>
            block.workspaceData?.category === "conditions",
        )
        .sort((a: BuildingBlock, b: BuildingBlock) =>
          a.label.localeCompare(b.label),
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

  // Sync allBlocks data to existing nodes when blocks finish loading
  useEffect(() => {
    if (allBlocksData.length > 0) {
      setNodes((prevNodes) =>
        prevNodes.map((node) => ({
          ...node,
          data: {
            ...node.data,
            allBlocks: allBlocksData,
          },
        })),
      );
    }
  }, [allBlocksData, setNodes]);

  // Trigger validation whenever yamlFlow changes
  useEffect(() => {
    // Only validate if yamlFlow has meaningful content
    if (yamlFlow.plan && yamlFlow.plan.length > 2) {
      const validationTimeout = setTimeout(() => {
        validateGraph();
      }, 100);

      return () => {
        clearTimeout(validationTimeout);
      };
    }
  }, [yamlFlow, validateGraph]);

  const isConnectionFeasible = useCallback(
    async (params: Connection): Promise<boolean> => {
      // Commenting out for now to allow all connections
      // try {
      //   const response = await axios.post("/graph/connection.feasible", {
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
    [setEdges, edges, nodes],
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    
    if (isDraggingCondition) {
      // For condition nodes, check if cursor is over a valid target node
      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - reactFlowBounds.left - 75,
        y: event.clientY - reactFlowBounds.top - 25,
      };

      const targetNode = nodes.find((node) => {
        const nodeWidth = 150;
        const nodeHeight = 80;
        
        return (
          position.x >= node.position.x - nodeWidth / 2 &&
          position.x <= node.position.x + nodeWidth / 2 &&
          position.y >= node.position.y - nodeHeight / 2 &&
          position.y <= node.position.y + nodeHeight / 2
        );
      });

      // Set different drop effects based on whether over a valid target
      event.dataTransfer.dropEffect = targetNode ? "copy" : "none";
    } else {
      // Regular nodes can be dropped anywhere
      event.dataTransfer.dropEffect = "move";
    }
  }, [nodes, isDraggingCondition]);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      // Reset drag state
      setIsDraggingCondition(false);

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const blockData = event.dataTransfer.getData("application/reactflow");

      if (blockData) {
        const block = JSON.parse(blockData);
        console.log(block);
        const position = {
          x: event.clientX - reactFlowBounds.left - 75,
          y: event.clientY - reactFlowBounds.top - 25,
        };

        // Check if this is a condition node
        const isConditionNode = block.workspaceData?.category === "conditions";

        if (isConditionNode) {
          // For condition nodes, check if dropping on an existing node
          const targetNode = nodes.find((node) => {
            // Calculate if drop position is within node bounds
            // Assuming standard node dimensions (approximately 150x80)
            const nodeWidth = 150;
            const nodeHeight = 80;
            
            return (
              position.x >= node.position.x - nodeWidth / 2 &&
              position.x <= node.position.x + nodeWidth / 2 &&
              position.y >= node.position.y - nodeHeight / 2 &&
              position.y <= node.position.y + nodeHeight / 2
            );
          });

          if (targetNode) {
            // Attach condition to the target node
            attachConditionToNode(targetNode.id, block);
          } else {
            // Show error message if not dropped on a node
            toast({
              title: "❌ Invalid Drop Location",
              description: "Condition nodes can only be dropped on existing nodes. Please drag the condition onto a node.",
              variant: "destructive",
            });
          }
          return; // Exit early for condition nodes
        }

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
            onDelete: stableDeleteNode,
            allBlocks: allBlocksRef.current,
            referencedConditions: [],
            onAttachCondition: stableAttachCondition,
            onRemoveCondition: stableRemoveCondition,
          },
        };

        const updatedNodes = [...nodes, newNode];
        setNodes(updatedNodes);
        setNodeId(nodeId + 1);

        // Update YAML flow with the new node
        setYamlFlow((prevFlow) => {
          const nodeRid = `$ref:${block.workspaceData?.rid || block.id}`;

          // Check if this node already exists in the nodes array
          const nodeExists = prevFlow.nodes.some(
            (node) => node.rid === nodeRid,
          );

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
          const updatedNodes = nodeExists
            ? prevFlow.nodes
            : [...prevFlow.nodes, newYamlNode];

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
    [nodeId, setNodes, nodes, stableDeleteNode, stableAttachCondition, stableRemoveCondition, toast],
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

  const handleEdgesChange = useCallback(
    (changes: any[]) => {
      onEdgesChange(changes);

      const selected = edges
        .filter((edge) => edge.selected)
        .map((edge) => edge.id);
      setSelectedEdges(selected);
    },
    [onEdgesChange, edges],
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
    
    // Set drag state based on block category
    const isCondition = block.workspaceData?.category === "conditions";
    setIsDraggingCondition(isCondition);
    
    event.dataTransfer.effectAllowed = isCondition ? "copy" : "move";

    const previewColor = themeColors.primary;
    const dragPreview = document.createElement("div");
    dragPreview.style.cssText = `
      position: absolute;
      top: -1000px;
      left: -1000px;
      padding: 8px 12px;
      background: ${previewColor};
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

  const onDragEnd = useCallback(() => {
    // Reset drag state when drag operation ends (whether successful or cancelled)
    setIsDraggingCondition(false);
  }, []);

  const clearGraph = () => {
    // Reset to default nodes instead of clearing completely
    initializeDefaultNodes();
    setEdges([]);

    // Reset YAML flow to default state
    setYamlFlow(defaulYmlState);

    // Reset validation state
    setIsGraphValid(false);
    setValidationResult(null);
    setFixSuggestions([]);

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

  const openSaveModal = () => {
    if (!isGraphValid) {
      toast({
        title: "❌ Cannot Save Invalid Graph",
        description:
          "Please fix all validation issues before saving the graph.",
        variant: "destructive",
      });
      return;
    }
    setSaveModalOpen(true);
  };

  const saveGraph = useCallback(
    async (name: string, description: string) => {
      try {
        setIsSaving(true);

        // Update yamlFlow with name and description
        const updatedYamlFlow = {
          ...yamlFlow,
          name: name,
          description: description,
        };

        setYamlFlow(updatedYamlFlow);

        // Convert to YAML string using js-yaml library
        const yamlString = yaml.dump(updatedYamlFlow, {
          indent: 2,
          lineWidth: -1,
          noRefs: true,
          sortKeys: false,
        });

        const response = await saveBlueprint(yamlString, USER_ID);

        if (response.status === "success") {
          // Show success toast
          toast({
            title: "✅ Blueprint Saved Successfully",
            description: `Blueprint "${name}" saved successfully`,
            variant: "default",
          });

          // Close the save modal immediately & Stop the saving state
          setSaveModalOpen(false);
          setIsSaving(false);

          // Call the onSaveComplete callback to navigate back (if provided)
          // Pass the saved blueprint info so it can be selected in the workflow list
          if (onSaveComplete) {
            setTimeout(() => {
              onSaveComplete({
                blueprintId: response.blueprint_id,
                name,
                description,
              });
            }, 100);
          }
        } else {
          throw new Error("Unknown error occurred while saving blueprint");
        }
      } catch (error) {
        console.error("Error saving graph:", error);
        toast({
          title: "❌ Error Saving Workflow",
          description: "Failed to save workflow to the server",
          variant: "destructive",
        });
        setIsSaving(false);
      }
    },
    [yamlFlow, toast, onSaveComplete],
  );

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Delete" || event.key === "Backspace") {
        const target = event.target as HTMLElement;
        if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
          return;
        }
        event.preventDefault();
        if (selectedNodes.length > 0) {
          selectedNodes.forEach((nodeId) => deleteNode(nodeId));
        }
        if (selectedEdges.length > 0) {
          selectedEdges.forEach((edgeId) => deleteEdge(edgeId));
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedNodes, selectedEdges, deleteNode, deleteEdge]);


  // --- Click-to-connect logic ---

  const cancelConnectionMode = useCallback(() => {
    setPendingConnectionSource(null);
    setNodes((prevNodes) =>
      prevNodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          isConnectionSource: false,
          isConnectionTarget: false,
        },
      })),
    );
  }, [setNodes]);

  const handleNodeClickForConnection = useCallback(
    (event: React.MouseEvent, node: Node) => {
      const target = event.target as HTMLElement;
      if (target.closest("button")) {
        return;
      }

      if (pendingConnectionSource === null) {
        setPendingConnectionSource(node.id);
        setNodes((prevNodes) =>
          prevNodes.map((n) => ({
            ...n,
            data: {
              ...n.data,
              isConnectionSource: n.id === node.id,
              isConnectionTarget: n.id !== node.id,
            },
          })),
        );
      } else if (pendingConnectionSource === node.id) {
        cancelConnectionMode();
      } else {
        const hasExisting = edges.some(
          (e) => e.source === pendingConnectionSource && e.target === node.id,
        );

        if (hasExisting) {
          toast({
            title: "Connection Already Exists",
            description: "This connection already exists.",
            variant: "destructive",
          });
        } else {
          const newEdge: Edge = {
            id: `${pendingConnectionSource}-${node.id}`,
            source: pendingConnectionSource,
            target: node.id,
            type: "custom",
            animated: true,
            style: { stroke: themeColors.primary, strokeWidth: 2 },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 20,
              height: 20,
              color: themeColors.primary,
            },
          };

          setEdges((prevEdges) => [...prevEdges, newEdge]);

          setYamlFlow((prevFlow) => {
            const updatedPlan = prevFlow.plan.map((step) => {
              if (step.uid === node.id) {
                const existingAfter = step.after;
                let newAfter;
                if (!existingAfter) {
                  newAfter = pendingConnectionSource;
                } else if (Array.isArray(existingAfter)) {
                  newAfter = existingAfter.includes(pendingConnectionSource!)
                    ? existingAfter
                    : [...existingAfter, pendingConnectionSource!];
                } else {
                  newAfter =
                    existingAfter === pendingConnectionSource
                      ? existingAfter
                      : [existingAfter, pendingConnectionSource!];
                }
                return { ...step, after: newAfter };
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
            edges: [...prev.edges, newEdge],
            metadata: {
              ...prev.metadata,
              lastModified: new Date(),
              edgeCount: prev.edges.length + 1,
            },
          }));
        }

        cancelConnectionMode();
      }
    },
    [pendingConnectionSource, nodes, edges, setNodes, cancelConnectionMode],
  );

  const handlePaneClick = useCallback(() => {
    if (pendingConnectionSource !== null) {
      cancelConnectionMode();
    }
  }, [pendingConnectionSource, cancelConnectionMode]);

  // ESC key handler for connection mode
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape" && pendingConnectionSource !== null) {
        cancelConnectionMode();
      }
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [pendingConnectionSource, cancelConnectionMode]);

  return {
    nodes,
    edges,
    currentGraph,
    buildingBlocksData,
    orchestratorsData,
    conditionsData,
    allBlocksData,
    isLoadingBlocks,
    yamlFlow,
    handleNodesChange,
    handleEdgesChange,
    onConnect,
    onDrop,
    onDragOver,
    onDragStart,
    onDragEnd,
    clearGraph,
    openSaveModal,
    saveGraph,
    deleteEdge,
    attachConditionToNode,
    removeConditionFromNode,
    // Click-to-connect
    pendingConnectionSource,
    handleNodeClickForConnection,
    handlePaneClick,
    cancelConnectionMode,
    // Drag state
    isDraggingCondition,
    // Validation state
    isGraphValid,
    validationResult,
    fixSuggestions,
    isValidating,
    validateGraph,
    // Save modal state
    saveModalOpen,
    setSaveModalOpen,
    isSaving,
  };
};
