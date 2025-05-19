import { useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import StatusBar from "@/components/layout/StatusBar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { motion } from "framer-motion";
import { Users, Network, Play } from "lucide-react";

// Agentic AI components
import AgentRepository from "@/components/agentic-ai/AgentRepository";
import AgentFlowGraph from "@/components/agentic-ai/AgentFlowGraph";
import ExecutionTab from "@/components/agentic-ai/ExecutionTab";

// Create a ReactFlow provider wrapper
import { ReactFlowProvider } from 'reactflow';

export default function AgenticAI() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("agent-repository");

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          title="Agentic AI System" 
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} 
        />
        
        <main className="flex-1 overflow-y-auto p-6 bg-background-dark">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Tabs 
              defaultValue="agent-repository" 
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <TabsList className="mb-6">
                <TabsTrigger
                  value="agent-repository"
                  className="data-[state=active]:bg-primary data-[state=active]:text-white"
                  onClick={() => setActiveTab("agent-repository")}
                >
                  <Users className="mr-2 h-4 w-4" />
                  Agent Repository
                </TabsTrigger>
                <TabsTrigger
                  value="agent-flow"
                  className="data-[state=active]:bg-primary data-[state=active]:text-white"
                  onClick={() => setActiveTab("agent-flow")}
                >
                  <Network className="mr-2 h-4 w-4" />
                  Agent Flow
                </TabsTrigger>
                <TabsTrigger
                  value="execution"
                  className="data-[state=active]:bg-primary data-[state=active]:text-white"
                  onClick={() => setActiveTab("execution")}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Execution
                </TabsTrigger>
              </TabsList>

              {/* Agent Repository Tab */}
              <TabsContent value="agent-repository" className="mt-0">
                <AgentRepository />
              </TabsContent>

              {/* Agent Flow Tab */}
              <TabsContent value="agent-flow" className="mt-0">
                <ReactFlowProvider>
                  <AgentFlowGraph />
                </ReactFlowProvider>
              </TabsContent>

              {/* Execution Tab */}
              <TabsContent value="execution" className="mt-0">
                <ExecutionTab />
              </TabsContent>
            </Tabs>
          </motion.div>
        </main>
        
        <StatusBar />
      </div>
    </div>
  );
}