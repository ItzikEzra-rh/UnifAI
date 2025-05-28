import { useState } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import StatusBar from "@/components/layout/StatusBar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { Users, Network, Play, Plus } from "lucide-react";

// Agentic AI components
import AgentRepository from "@/components/agentic-ai/AgentRepository";
import AgentFlowGraph from "@/components/agentic-ai/AgentFlowGraph";
import ExecutionTab from "@/components/agentic-ai/ExecutionTab";
import { StreamingDataProvider } from "@/components/agentic-ai/StreamingDataContext";
import { FlowObject } from '../components/agentic-ai/graphs/interfaces'
import axios from '../http/axiosAgentConfig'

// Create a ReactFlow provider wrapper
import { ReactFlowProvider } from 'reactflow';

export interface GraphNode {
  id: string;
  name: string;
  description: string | null;
}

export default function AgenticAI() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("agent-repository");
  const [selectedFlow, setSelectedFlow] = useState<FlowObject | null>(null);
  const [builtGraphId, setBuiltGraphId] = useState<string | null>(null);
  const [builtGraphName, setBuiltGraphName] = useState<string | null>(null);
  const [selectedGraphId, setSelectedGraphId] = useState<string | null>(null);
  const [selectedGraphNodes, setSelectedGraphNodes] = useState<GraphNode[] | null>(null);

  const handleBuildGraph = async () => {
    try {
      const graphId = selectedFlow?.id || `graph-${Date.now()}`;
      const graphName = selectedFlow?.name || "Custom Flow " + Math.floor(Math.random() * 1000);
      const agentNodes = selectedFlow?.flow.nodes.map(node => ({
        'id': node.id,
        'name': node.data.label,
        'description': node.data.description,
      })) || null

      setSelectedGraphNodes(agentNodes)
      
      // Set the graph ID and name
      setBuiltGraphId(graphId);
      setBuiltGraphName(graphName);

      const selectedBlueprint = {
        'blueprintId': graphId,
        'userId': "alice",
      }

      const response = await axios.post('/api/sessions/user.session.create', selectedBlueprint);
      setSelectedGraphId(response.data)

      // Switch to the Execution tab
      setActiveTab("execution");
    } catch (error) {
      console.error('Error create new graph session:', error);
    }
  };

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
                <Card className="bg-background-card shadow-card border-gray-800 mb-6">
                  <CardHeader className="py-2 px-6 flex flex-row justify-between items-center">
                    <CardTitle className="text-lg font-heading">Agent Flow Configuration</CardTitle>
                    <Button
                      className="bg-[#8A2BE2] hover:bg-opacity-80 flex items-center gap-2"
                      size="sm"
                      onClick={handleBuildGraph}
                    >
                      <Plus className="h-4 w-4" />
                      Build Graph
                    </Button>
                  </CardHeader>
                  <CardContent className="pt-2 px-4 pb-4">
                    <p className="text-sm text-gray-400">
                      Configure your agent workflow and build a graph to execute with the Agentic AI system.
                      Click "Build Graph" to create a runnable graph and start execution.
                    </p>
                  </CardContent>
                </Card>
                
                <ReactFlowProvider>
                  <AgentFlowGraph selectedFlow={selectedFlow} setSelectedFlow={setSelectedFlow} />
                </ReactFlowProvider>
              </TabsContent>

              {/* Execution Tab */}
              <TabsContent value="execution" className="mt-0">
                {/* TODO: Don't allow the user to chat with the model if there isn't any active 'builtGraphId' */}
                {builtGraphId && (
                  <div className="mb-4 px-4 py-3 bg-[#8A2BE2] bg-opacity-10 border border-[#8A2BE2] rounded-md">
                    <p className="text-sm">
                      <span className="font-medium">Active Graph:</span> {builtGraphName} <span className="text-xs text-gray-400 ml-2">(ID: {builtGraphId})</span>
                    </p>
                  </div>
                )}
                <StreamingDataProvider>
                  <ExecutionTab runId={selectedGraphId} selectedGraphNodes={selectedGraphNodes} />
                </StreamingDataProvider>
              </TabsContent>
            </Tabs>
          </motion.div>
        </main>
        
        <StatusBar />
      </div>
    </div>
  );
}