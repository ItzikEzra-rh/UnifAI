import React, { useState } from 'react';
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import GraphCanvas from '@/components/graph/GraphCanvas';
import BuildingBlocksSidebar from '@/components/graph/BuildingBlocksSidebar';
import { useGraphLogic } from '@/hooks/use-graph-logic';

export default function NewGraph() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const {
    nodes,
    edges,
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
  } = useGraphLogic();

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="New Graph Builder" onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}/>

        <main className="flex-1 overflow-hidden p-4 bg-background-dark">
          <div className="flex h-full gap-4">
            <GraphCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={handleNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onClearGraph={clearGraph}
              onSaveGraph={saveGraph}
            />

            <BuildingBlocksSidebar 
              buildingBlocks={buildingBlocksData}
              isLoading={isLoadingBlocks}
              onDragStart={onDragStart} 
            />
          </div>
        </main>
      </div>
    </div>
  );
} 