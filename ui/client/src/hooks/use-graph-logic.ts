import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { useToast } from "@/hooks/use-toast";
import { CurrentGraph, BuildingBlock, CanvasNode, CanvasEdge } from "@/types/graph";
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
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [edges, setEdges] = useState<CanvasEdge[]>([]);
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
              // Clean up `after` on the target step (forward edges)
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
              }

              // Clean up `branches` on the source step (back-edges)
              if (step.uid === removedEdge.source && step.branches) {
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
    const userInputNode: CanvasNode = {
      id: "user_input",
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

    const finalizeNode: CanvasNode = {
      id: "finalize",
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

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    
    if (isDraggingCondition) {
      const canvasBoundsRect = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - canvasBoundsRect.left - 75,
        y: event.clientY - canvasBoundsRect.top - 25,
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

      const canvasBounds = event.currentTarget.getBoundingClientRect();
      const blockData = event.dataTransfer.getData("application/reactflow");

      if (blockData) {
        const block = JSON.parse(blockData);
        const position = {
          x: event.clientX - canvasBounds.left - 75,
          y: event.clientY - canvasBounds.top - 25,
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
        const newNode: CanvasNode = {
          id: nodeUid,
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

  const selectNode = useCallback(
    (nodeId: string | null) => {
      setNodes((prev) =>
        prev.map((n) => ({ ...n, selected: n.id === nodeId })),
      );
      setSelectedNodes(nodeId ? [nodeId] : []);
    },
    [setNodes],
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
        selected: false,
        data: {
          ...n.data,
          isConnectionSource: false,
          isConnectionTarget: false,
        },
      })),
    );
  }, [setNodes]);

  const handleNodeClickForConnection = useCallback(
    (clickedNodeId: string) => {
      if (pendingConnectionSource === null) {
        setPendingConnectionSource(clickedNodeId);
        setNodes((prevNodes) =>
          prevNodes.map((n) => ({
            ...n,
            data: {
              ...n.data,
              isConnectionSource: n.id === clickedNodeId,
              isConnectionTarget: n.id !== clickedNodeId,
            },
          })),
        );
      } else if (pendingConnectionSource === clickedNodeId) {
        cancelConnectionMode();
      } else {
        const hasExisting = edges.some(
          (e) => e.source === pendingConnectionSource && e.target === clickedNodeId,
        );

        if (hasExisting) {
          toast({
            title: "Connection Already Exists",
            description: "This connection already exists.",
            variant: "destructive",
          });
        } else {
          const sourceNode = nodes.find((n) => n.id === pendingConnectionSource);
          const hasCondition =
            sourceNode?.data?.referencedConditions &&
            sourceNode.data.referencedConditions.length > 0;

          if (hasCondition) {
            // Source node has a condition — create a conditional/branch
            // edge (uses `branches` on the source step, NOT `after` on
            // the target). This mirrors the old createConditionalEdge.
            const condition = sourceNode.data.referencedConditions[0];
            const conditionType =
              condition.workspaceData?.type || condition.type;

            const newEdge: CanvasEdge = {
              id: `${pendingConnectionSource}-${clickedNodeId}`,
              source: pendingConnectionSource,
              target: clickedNodeId,
              data: { isConditional: true },
            };

            setEdges((prevEdges) => [...prevEdges, newEdge]);

            setYamlFlow((prevFlow) => {
              const conditionRid =
                condition.workspaceData?.rid || condition.id;

              const updatedPlan = prevFlow.plan.map((step) => {
                if (step.uid === pendingConnectionSource) {
                  const existingBranches = step.branches || {};
                  const newBranches = { ...existingBranches };

                  if (conditionType === "router_direct") {
                    newBranches[clickedNodeId] = clickedNodeId;
                  } else if (conditionType === "router_boolean") {
                    if (!newBranches["true"] && !newBranches[true as any]) {
                      newBranches["true"] = clickedNodeId;
                    } else if (
                      !newBranches["false"] &&
                      !newBranches[false as any]
                    ) {
                      newBranches["false"] = clickedNodeId;
                    } else {
                      let n = 2;
                      while (newBranches[`branch_${n}`]) n++;
                      newBranches[`branch_${n}`] = clickedNodeId;
                    }
                  } else {
                    // Generic condition type — auto-assign branch keys
                    const usedKeys = new Set(Object.keys(newBranches));
                    let branchKey = "true";
                    if (usedKeys.has("true")) branchKey = "false";
                    if (usedKeys.has("true") && usedKeys.has("false")) {
                      let n = 2;
                      while (usedKeys.has(`branch_${n}`)) n++;
                      branchKey = `branch_${n}`;
                    }
                    newBranches[branchKey] = clickedNodeId;
                  }

                  return {
                    ...step,
                    exit_condition: conditionRid,
                    branches: newBranches,
                  };
                }
                return step;
              });

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
                nodes: prevFlow.nodes,
                conditions:
                  updatedConditions.length > 0 ? updatedConditions : [],
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
          } else {
            // Source has no condition — regular edge using `after`.
            const newEdge: CanvasEdge = {
              id: `${pendingConnectionSource}-${clickedNodeId}`,
              source: pendingConnectionSource,
              target: clickedNodeId,
            };

            setEdges((prevEdges) => [...prevEdges, newEdge]);

            setYamlFlow((prevFlow) => {
              const updatedPlan = prevFlow.plan.map((step) => {
                if (step.uid === clickedNodeId) {
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
        }

        cancelConnectionMode();
      }
    },
    [pendingConnectionSource, edges, nodes, setNodes, cancelConnectionMode, toast],
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

  const updateNodePosition = useCallback(
    (nodeId: string, position: { x: number; y: number }) => {
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, position } : n)),
      );
    },
    [setNodes],
  );

  return {
    nodes,
    edges,
    setNodes,
    setEdges,
    currentGraph,
    buildingBlocksData,
    orchestratorsData,
    conditionsData,
    allBlocksData,
    isLoadingBlocks,
    yamlFlow,
    selectNode,
    onDrop,
    onDragOver,
    onDragStart,
    onDragEnd,
    clearGraph,
    openSaveModal,
    saveGraph,
    deleteNode,
    deleteEdge,
    attachConditionToNode,
    removeConditionFromNode,
    updateNodePosition,
    pendingConnectionSource,
    handleNodeClickForConnection,
    handlePaneClick,
    cancelConnectionMode,
    isDraggingCondition,
    isGraphValid,
    validationResult,
    fixSuggestions,
    isValidating,
    validateGraph,
    saveModalOpen,
    setSaveModalOpen,
    isSaving,
  };
};
