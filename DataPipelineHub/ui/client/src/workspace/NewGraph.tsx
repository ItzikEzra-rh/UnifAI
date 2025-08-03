import React, { useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import BuildingBlocksSidebar from "@/workspace/BuildingBlocksSidebar";
import { useGraphLogic } from "@/hooks/use-graph-logic";
import GraphCanvas from "@/components/agentic-ai/graphs/GraphCanvas";
import ConditionalEdgeModal from "@/components/agentic-ai/graphs/ConditionalEdgeModal";
import { MarkerType } from "reactflow";

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
  } = useGraphLogic();

  const handleSaveGraph = async () => {
    await saveGraph();
    if (onBack) onBack();
  };

  const handleClearGraph = () => {
    clearGraph();
  };

  return (
    <main className="flex-1 overflow-hidden p-4 bg-background-dark">
      <div className="flex h-full gap-4">
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
          conditionalEdgeModal={conditionalEdgeModal}
          onConditionalEdgeConfirm={handleConditionalEdgeConfirm}
          onConditionalEdgeCancel={handleConditionalEdgeCancel}
        />

        <BuildingBlocksSidebar
          buildingBlocks={buildingBlocksData}
          conditions={conditionsData}
          isLoading={isLoadingBlocks}
          onDragStart={onDragStart}
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
    </main>
  );
}
