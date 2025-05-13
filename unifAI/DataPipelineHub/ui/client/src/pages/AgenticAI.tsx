import { useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import StatusBar from "@/components/layout/StatusBar";
import { Card } from "@/components/ui/card";
import { motion } from "framer-motion";

// Agentic AI components
import AgentFlowGraph from "@/components/agentic-ai/AgentFlowGraph";
import ChatInterface from "@/components/agentic-ai/ChatInterface";
import ExecutionStream from "@/components/agentic-ai/ExecutionStream";

// Create a ReactFlow provider wrapper
import { ReactFlowProvider } from 'reactflow';

export default function AgenticAI() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          title="Agentic AI System" 
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} 
        />
        
        <main className="flex-1 overflow-y-auto p-6 bg-background-dark">
          {/* Agent Flow Graph */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-6"
          >
            <ReactFlowProvider>
              <AgentFlowGraph />
            </ReactFlowProvider>
          </motion.div>
          
          {/* Chat and Execution Stream - Side by Side on Desktop, Stacked on Mobile */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
            style={{ height: 'calc(50vh - 2rem)' }}
          >
            <div className="h-full">
              <ChatInterface />
            </div>
            <div className="h-full">
              <ExecutionStream />
            </div>
          </motion.div>
        </main>
        
        <StatusBar />
      </div>
    </div>
  );
}