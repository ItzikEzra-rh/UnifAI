import React, { useState } from "react";
import { useGraphLogic } from "@/hooks/use-graph-logic";
import GraphCanvas from "@/components/agentic-ai/graphs/GraphCanvas";
import BuildingBlocksSidebar from "./BuildingBlocksSidebar";
import ConditionalEdgeModal from "@/components/agentic-ai/graphs/ConditionalEdgeModal";
import GraphValidationPanel from "@/components/agentic-ai/graphs/GraphValidationPanel";
import SaveBlueprintModal from "@/components/agentic-ai/graphs/SaveBlueprintModal";

interface NewGraphProps {
  onBack?: () => void;
}

export default function NewGraph({ onBack }: NewGraphProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const {
    nodes,
    edges,
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
    isGraphValid,
    validationResult,
    fixSuggestions,
    isValidating,
    isSaving,
  } = useGraphLogic();

  const [saveModalOpen, setSaveModalOpen] = useState(false);

  const handleSaveGraph = async () => {
    setSaveModalOpen(true);
  };

  const handleClearGraph = () => {
    clearGraph();
  };

  return (
    <div className="h-full max-h-[calc(100vh-100px)] flex bg-background overflow-hidden">
      {/* Sidebar */}
      <div className="w-80 h-full">
        <BuildingBlocksSidebar
          buildingBlocks={buildingBlocksData}
          conditions={conditionsData}
          isLoading={isLoadingBlocks}
          onDragStart={onDragStart}
        />
      </div>

      {/* Main Canvas */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <GraphCanvas
          nodes={nodes}
          edges={edges}
          yamlFlow={yamlFlow}
          onNodesChange={handleNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onClearGraph={handleClearGraph}
          onSaveGraph={handleSaveGraph}
          onBack={onBack}
          onAttachCondition={attachConditionToNode}
          onRemoveCondition={removeConditionFromNode}
          isGraphValid={isGraphValid}
        />
      </div>

      {/* Validation Panel */}
      <div className="w-80 h-full">
        <GraphValidationPanel
          validationResult={validationResult}
          fixSuggestions={fixSuggestions}
          isValidating={isValidating}
        />
      </div>

      
      <ConditionalEdgeModal
        isOpen={conditionalEdgeModal.isOpen}
        onClose={handleConditionalEdgeCancel}
        onConfirm={handleConditionalEdgeConfirm}
        sourceNodeId={conditionalEdgeModal.sourceNodeId}
        targetNodeId={conditionalEdgeModal.targetNodeId}
        conditionType={conditionalEdgeModal.conditionType}
        existingBranches={conditionalEdgeModal.existingBranches}
      />

      {/* Save Blueprint Modal */}
      <SaveBlueprintModal
        isOpen={saveModalOpen}
        onClose={() => setSaveModalOpen(false)}
        onSave={saveGraph}
        isLoading={isSaving}
      />
    </div>
  );
}
