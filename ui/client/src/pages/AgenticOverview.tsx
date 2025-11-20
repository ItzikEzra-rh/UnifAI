import { useState } from "react";
import { FaProjectDiagram, FaChartPie, FaPlayCircle, FaBoxes, FaChevronRight } from "react-icons/fa";
import { useProject } from "@/contexts/ProjectContext";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";

// Layout components
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import StatusBar from "@/components/layout/StatusBar";

// Agentic Overview components
import GlassPanel from "@/components/ui/GlassPanel";
import { useQuery } from "@tanstack/react-query";
import { fetchAgenticStats, fetchWorkflows, fetchActiveSessions, fetchAllResources, fetchBlueprintSessionCounts, WorkflowBlueprint } from "@/api/agentic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTheme } from "@/contexts/ThemeContext";
import { Workflow, Database, Users, Zap, TrendingUp, Clock, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import ReactFlowGraph from "@/components/agentic-ai/graphs/ReactFlowGraph";
import { ReactFlowProvider } from "reactflow";
import SimpleTooltip from "@/components/shared/SimpleTooltip";

export default function AgenticOverview() {
  const { projects } = useProject();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowBlueprint | null>(null);
  const [isWorkflowModalOpen, setIsWorkflowModalOpen] = useState(false);
  const { primaryHex } = useTheme();
  const { user } = useAuth();
  const userId = user?.username || "default";

  // Fetch agentic AI stats
  const { data: agenticStats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['agenticStats', userId],
    queryFn: () => fetchAgenticStats(userId),
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
  });

  // Fetch workflows
  const { data: workflows = [], isLoading: isLoadingWorkflows } = useQuery({
    queryKey: ['workflows', userId],
    queryFn: () => fetchWorkflows(userId),
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
  });

  // Fetch active sessions
  const { data: activeSessions = [], isLoading: isLoadingSessions } = useQuery({
    queryKey: ['activeSessions', userId],
    queryFn: () => fetchActiveSessions(userId),
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });

  // Fetch session counts by blueprint_id
  const { data: blueprintSessionCounts = {}, isLoading: isLoadingCounts } = useQuery({
    queryKey: ['blueprintSessionCounts', userId],
    queryFn: () => fetchBlueprintSessionCounts(userId),
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });

  // Fetch resources
  const { data: resources = [], isLoading: isLoadingResources } = useQuery({
    queryKey: ['allResources', userId],
    queryFn: () => fetchAllResources(userId),
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
  });

  // Calculate resource distribution
  const resourceDistribution = agenticStats?.resourcesByCategory || [];
  const topCategories = resourceDistribution
    .sort((a, b) => b.count - a.count)
    .slice(0, 3);

  // Filter unused workflows (workflows not in active sessions)
  const unusedWorkflows = workflows.filter(
    workflow => !activeSessions.includes(workflow.blueprint_id)
  );

  // Calculate most used workflows (workflows that are currently active)
  const mostUsedWorkflows = workflows
    .filter(workflow => (blueprintSessionCounts[workflow.blueprint_id] || 0) > 0)
    .map(workflow => ({
      ...workflow,
      usageCount: blueprintSessionCounts[workflow.blueprint_id] || 0
    }))
    .sort((a, b) => b.usageCount - a.usageCount)
    .slice(0, 5);

  // Handle workflow click
  const handleWorkflowClick = (workflow: WorkflowBlueprint) => {
    setSelectedWorkflow(workflow);
    setIsWorkflowModalOpen(true);
  };

  // Handle modal close
  const handleCloseModal = () => {
    setIsWorkflowModalOpen(false);
    setSelectedWorkflow(null);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header title="Agentic AI Overview" onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-transparent">
          {/* Top row: Key Metrics */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mb-6 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6"
          >
            {/* Total Workflows */}
            <GlassPanel className="h-full">
              <Card className="rounded-xl border-0 shadow-none bg-transparent">
                <div className="relative p-4 border-b border-border">
                  <div className="absolute top-2 right-4 w-8 h-8 rounded-lg bg-primary/20 text-primary flex items-center justify-center">
                    <Workflow className="w-4 h-4" />
                  </div>
                  <h3 className="text-lg font-semibold text-white flex items-center">
                    <FaProjectDiagram className="text-primary mr-3 h-5 w-5" />
                    Workflows
                  </h3>
                </div>
                <CardContent className="p-4">
                  {isLoadingStats ? (
                    <div className="flex items-center justify-center h-16">
                      <Loader2 className="w-6 h-6 animate-spin text-primary" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-3xl font-bold text-white">{agenticStats?.totalWorkflows || 0}</p>
                      <p className="text-xs text-gray-400">Total blueprints available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </GlassPanel>

            {/* Active Sessions */}
            <GlassPanel className="h-full">
              <Card className="rounded-xl border-0 shadow-none bg-transparent">
                <div className="relative p-4 border-b border-border">
                  <div className="absolute top-2 right-4 w-8 h-8 rounded-lg bg-green-500/20 text-green-500 flex items-center justify-center">
                    <Zap className="w-4 h-4" />
                  </div>
                  <h3 className="text-lg font-semibold text-white flex items-center">
                    <FaPlayCircle className="text-green-500 mr-3 h-5 w-5" />
                    Active Sessions
                  </h3>
                </div>
                <CardContent className="p-4">
                  {isLoadingSessions ? (
                    <div className="flex items-center justify-center h-16">
                      <Loader2 className="w-6 h-6 animate-spin text-green-500" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-3xl font-bold text-white">{agenticStats?.activeSessions || 0}</p>
                      <p className="text-xs text-gray-400">Currently running</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </GlassPanel>

            {/* Total Resources */}
            <GlassPanel className="h-full">
              <Card className="rounded-xl border-0 shadow-none bg-transparent">
                <div className="relative p-4 border-b border-border">
                  <div className="absolute top-2 right-4 w-8 h-8 rounded-lg bg-secondary/20 text-secondary flex items-center justify-center">
                    <Database className="w-4 h-4" />
                  </div>
                  <h3 className="text-lg font-semibold text-white flex items-center">
                    <FaBoxes className="text-secondary mr-3 h-5 w-5" />
                    Inventory
                  </h3>
                </div>
                <CardContent className="p-4">
                  {isLoadingResources ? (
                    <div className="flex items-center justify-center h-16">
                      <Loader2 className="w-6 h-6 animate-spin text-secondary" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-3xl font-bold text-white">{agenticStats?.totalResources || 0}</p>
                      <p className="text-xs text-gray-400">Total resources configured</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </GlassPanel>

            {/* Resource Categories */}
            <GlassPanel className="h-full">
              <Card className="rounded-xl border-0 shadow-none bg-transparent">
                <div className="relative p-4 border-b border-border">
                  <div className="absolute top-2 right-4 w-8 h-8 rounded-lg bg-purple-500/20 text-purple-500 flex items-center justify-center">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                  <h3 className="text-lg font-semibold text-white flex items-center">
                    <FaChartPie className="text-purple-500 mr-3 h-5 w-5" />
                    Categories
                  </h3>
                </div>
                <CardContent className="p-4">
                  {isLoadingStats ? (
                    <div className="flex items-center justify-center h-16">
                      <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-3xl font-bold text-white">{resourceDistribution.length}</p>
                      <p className="text-xs text-gray-400">Resource categories</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </GlassPanel>
          </motion.div>

          {/* Middle row: Resource Distribution */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-8"
          >
            {/* Resource Distribution Chart */}
            <GlassPanel style={{ height: 400 }}>
              <Card className="shadow-card border-gray-800 h-full flex flex-col bg-transparent border-0">
                <CardHeader className="py-4 px-6">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl flex items-center gap-2">
                      <FaChartPie className="text-primary" />
                      Resource Distribution
                    </CardTitle>
                    <span className="text-sm text-gray-400">By Category</span>
                  </div>
                </CardHeader>
                <CardContent className="px-6 pb-6 flex-1 overflow-hidden flex flex-col min-h-0">
                  {isLoadingStats ? (
                    <div className="flex items-center justify-center h-full">
                      <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                  ) : resourceDistribution.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400">
                      No resources configured yet
                    </div>
                  ) : (
                    <div className="space-y-4 overflow-y-auto flex-1 pr-2 pb-4">
                      {resourceDistribution
                        .sort((a, b) => b.count - a.count)
                        .slice(0, 5)
                        .map((category, idx) => {
                          const total = resourceDistribution.reduce((sum, c) => sum + c.count, 0);
                          const percentage = total > 0 ? Math.round((category.count / total) * 100) : 0;
                          const colors = [
                            primaryHex || "#A60000",
                            "hsl(var(--secondary))",
                            "#8B5CF6",
                            "#10B981",
                            "#F59E0B"
                          ];
                          const color = colors[idx % colors.length];
                          
                          // Create tooltip content with type breakdown
                          const typeBreakdown = Object.entries(category.types)
                            .map(([type, count]) => `${count} ${type}`)
                            .join(', ');
                          const tooltipContent = typeBreakdown || 'No sub-types';

                          return (
                            <SimpleTooltip content={<div className="text-sm">{tooltipContent}</div>}>
                              <div key={category.category} className="space-y-2 max-h-24 overflow-hidden flex flex-col cursor-help">
                                <div className="flex items-center justify-between text-sm flex-shrink-0">
                                  <span className="text-gray-300 font-medium">{category.category}</span>
                                  <span className="text-gray-400">{category.count} ({percentage}%)</span>
                                </div>
                                <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden flex-shrink-0">
                                  <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${percentage}%` }}
                                    transition={{ duration: 0.8, delay: idx * 0.1 }}
                                    className="h-full rounded-full"
                                    style={{ backgroundColor: color }}
                                  />
                                </div>
                              </div>
                            </SimpleTooltip>
                          );
                        })}
                    </div>
                  )}
                </CardContent>
              </Card>
            </GlassPanel>
          </motion.div>

          {/* Bottom row: Most Used Workflows and Unused Available Workflows */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mb-8 grid grid-cols-1 xl:grid-cols-2 gap-6"
          >
            {/* Most Used Workflows */}
            <GlassPanel style={{ height: 340 }}>
              <Card className="shadow-card border-gray-800 bg-transparent border-0 flex flex-col h-full">
                <CardHeader className="py-4 px-6 flex-shrink-0">
                  <CardTitle className="text-xl flex items-center gap-2">
                    <FaProjectDiagram className="text-primary" />
                    Most Used Workflows
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col min-h-0 px-6 pb-6">
                  {isLoadingWorkflows || isLoadingSessions || isLoadingCounts ? (
                    <div className="flex items-center justify-center h-full">
                      <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                  ) : mostUsedWorkflows.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                      No workflows currently in use
                    </div>
                  ) : (
                    <div className="space-y-3 pr-2">
                      {mostUsedWorkflows.map((workflow, idx) => (
                        <motion.div
                          key={workflow.blueprint_id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          onClick={() => handleWorkflowClick(workflow)}
                          className="p-3 bg-gray-800/50 rounded-lg border border-gray-700 hover:border-primary/50 transition-colors cursor-pointer group flex-shrink-0"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="w-8 h-8 rounded-lg bg-primary/20 text-primary flex items-center justify-center shrink-0">
                                <Workflow className="w-4 h-4" />
                              </div>
                              <div className="min-w-0 flex-1 overflow-hidden">
                                <p className="text-sm font-medium text-white truncate">
                                  {workflow.spec_dict?.name || workflow.blueprint_id}
                                </p>
                                <p className="text-xs text-gray-400 truncate">
                                  {workflow.blueprint_id}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <span className="text-xs text-gray-400">{workflow.usageCount}x</span>
                              <FaChevronRight className="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </GlassPanel>

            {/* Unused Available Workflows */}
            <GlassPanel style={{ height: 340 }}>
              <Card className="shadow-card border-gray-800 bg-transparent border-0 flex flex-col h-full">
                <CardHeader className="py-4 px-6 flex-shrink-0">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl flex items-center gap-2">
                      <FaProjectDiagram className="text-primary" />
                      Unused Available Workflows
                    </CardTitle>
                    <span className="text-sm text-gray-400">{unusedWorkflows.length}</span>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col min-h-0 px-6 pb-6">
                  {isLoadingWorkflows || isLoadingSessions || isLoadingCounts ? (
                    <div className="flex items-center justify-center h-full">
                      <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                  ) : unusedWorkflows.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                      {workflows.length === 0 
                        ? "No workflows available" 
                        : "All workflows are currently in use"}
                    </div>
                  ) : (
                    <div className="space-y-3 pr-2">
                      {unusedWorkflows.slice(0, 8).map((workflow, idx) => (
                        <motion.div
                          key={workflow.blueprint_id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          onClick={() => handleWorkflowClick(workflow)}
                          className="p-3 bg-gray-800/50 rounded-lg border border-gray-700 hover:border-primary/50 transition-colors cursor-pointer group flex-shrink-0"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="w-8 h-8 rounded-lg bg-primary/20 text-primary flex items-center justify-center shrink-0">
                                <Workflow className="w-4 h-4" />
                              </div>
                              <div className="min-w-0 flex-1 overflow-hidden">
                                <p className="text-sm font-medium text-white truncate">
                                  {workflow.spec_dict?.name || workflow.blueprint_id}
                                </p>
                                <p className="text-xs text-gray-400 truncate">
                                  {workflow.blueprint_id}
                                </p>
                              </div>
                            </div>
                            <FaChevronRight className="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors shrink-0" />
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </GlassPanel>
          </motion.div>
        </main>
        <StatusBar />
      </div>

      {/* Workflow View Modal */}
      <Dialog open={isWorkflowModalOpen} onOpenChange={handleCloseModal}>
        <DialogContent className="bg-background-card border-gray-800 max-w-6xl w-[90vw] h-[85vh] flex flex-col p-0 overflow-hidden">
          <DialogHeader className="px-6 py-4 border-b border-gray-800 flex-shrink-0">
            <DialogTitle className="text-xl flex items-center gap-2">
              <FaProjectDiagram className="text-primary" />
              {selectedWorkflow?.spec_dict?.name || selectedWorkflow?.blueprint_id || "Workflow View"}
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-hidden p-6 min-h-0">
            {selectedWorkflow && (
              <ReactFlowProvider>
                <div className="h-full w-full">
                  <ReactFlowGraph
                    blueprintId={selectedWorkflow.blueprint_id}
                    height="100%"
                    showControls={true}
                    showMiniMap={true}
                    showBackground={true}
                    interactive={true}
                    isLiveRequest={false}
                  />
                </div>
              </ReactFlowProvider>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

