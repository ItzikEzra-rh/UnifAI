import React, { useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import BuildingBlocksSidebar from "@/workspace/BuildingBlocksSidebar";
import { useGraphLogic } from "@/hooks/use-graph-logic";
import GraphCanvas from "@/components/agentic-ai/graphs/GraphCanvas";

interface NewGraphProps {
  onBack?: () => void;
}

export default function NewGraph({ onBack }: NewGraphProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const {
    nodes,
    edges,
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
        />

        <BuildingBlocksSidebar
          buildingBlocks={buildingBlocksData}
          isLoading={isLoadingBlocks}
          onDragStart={onDragStart}
        />
      </div>
    </main>
  );
}
