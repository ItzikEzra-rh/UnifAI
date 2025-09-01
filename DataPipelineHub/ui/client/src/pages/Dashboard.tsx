import { useState } from "react";
import { FaStream, FaPlug, FaChartPie, FaProjectDiagram, FaRobot, FaDatabase, FaChevronRight } from "react-icons/fa";
import { useProject } from "@/contexts/ProjectContext";
import { motion } from "framer-motion";

// Layout components
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import StatusBar from "@/components/layout/StatusBar";

// Dashboard components
import StatusCard from "@/components/dashboard/StatusCard";
import { PipelineVisualizerWrapper } from "@/components/dashboard/PipelineVisualizerWrapper";
import ProjectCard from "@/components/dashboard/ProjectCard";
import { LiveActivityFeed } from "@/components/dashboard/LiveActivityFeed";
import DataSourceStats from "@/components/dashboard/DataSourceStats";
import { PipelineInfoCards } from "@/components/dashboard/PipelineInfoCards";
import GlassPanel from "@/components/ui/GlassPanel";
import { useQuery } from "@tanstack/react-query";
import { fetchActivePipelines, fetchPipelineMetrics, fetchConnectedSources } from "@/api/pipelines";
import { PIPELINE_STATUS } from "@/constants/pipelineStatus";
import { PieChart, Pie, Cell } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip } from "@/components/ui/chart";
import { Separator } from "@/components/ui/separator";

export default function Dashboard() {
  const { projects } = useProject();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Live metrics for summary cards
  const { data: metrics } = useQuery({
    queryKey: ['pipelineMetricsSummary'],
    queryFn: fetchPipelineMetrics,
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });

  const { data: connectedSources } = useQuery({
    queryKey: ['connectedSourcesSummary'],
    queryFn: fetchConnectedSources,
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
  });

  const slackCount = connectedSources?.byType?.slack ?? 0;
  const documentCount = connectedSources?.byType?.document ?? 0;
  const totalSources = slackCount + documentCount;

  const { data: activePipelines = [] } = useQuery({
    queryKey: ['activePipelinesListSummary'],
    queryFn: fetchActivePipelines,
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });

  const processingCount = activePipelines.filter(p => [
    PIPELINE_STATUS.COLLECTING,
    PIPELINE_STATUS.PROCESSING,
    PIPELINE_STATUS.CHUNKING_AND_EMBEDDING,
    PIPELINE_STATUS.STORING,
    PIPELINE_STATUS.ORCHESTRATING,
  ].includes(p.status as any)).length;

  const waitingCount = activePipelines.filter(p => p.status === PIPELINE_STATUS.PENDING || p.status === PIPELINE_STATUS.ACTIVE).length;
  const pausedCount = activePipelines.filter(p => p.status === PIPELINE_STATUS.PAUSED).length;

  const totalDocs = activePipelines.reduce((sum, p) => sum + (p.pipeline_stats?.documents_retrieved || 0), 0);
  const totalEmbeddings = activePipelines.reduce((sum, p) => sum + (p.pipeline_stats?.embeddings_created || 0), 0);
  const totalProcessingTime = activePipelines.reduce((sum, p) => sum + (p.pipeline_stats?.processing_time || 0), 0);
  const docsPerMin = totalProcessingTime > 0 ? Math.round((totalDocs / totalProcessingTime) * 60) : 0;
  
  // Data source stats
  const dataSourceStats = {
    totalVectors: '26.7K',
    stats: [
      { source: 'Jira Issues', color: 'primary', count: '12.3K', percentage: 45 },
      { source: 'Slack Messages', color: 'secondary', count: '8.2K', percentage: 30 },
      { source: 'Documents', color: 'accent', count: '6.7K', percentage: 25 }
    ]
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header title="Overview Dashboard" onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-transparent">
          {/* Top row: Processing Stats and Connected Sources side-by-side */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mb-6 grid grid-cols-1 xl:grid-cols-3 gap-6"
          >
            <GlassPanel className="h-full">
              <PipelineInfoCards metrics={metrics} activePipelines={activePipelines} showProcessing showConnected={false} showActive={false} />
            </GlassPanel>
            <GlassPanel className="h-full">
              <PipelineInfoCards metrics={metrics} activePipelines={activePipelines} showProcessing={false} showConnected showActive={false} />
            </GlassPanel>
            <GlassPanel className="h-full">
              <PipelineInfoCards metrics={metrics} activePipelines={activePipelines} showProcessing={false} showConnected={false} showActive={false} showLastSync />
            </GlassPanel>
          </motion.div>

          {/* Middle row: Pipeline tracker left, Connected Sources right (same line) */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-8 grid grid-cols-1 xl:grid-cols-3 gap-6"
          >
            <GlassPanel strong className="xl:col-span-2">
              <PipelineVisualizerWrapper />
            </GlassPanel>
            <GlassPanel className="xl:col-span-1" style={{ height: 500 }}>
              <Card className=" shadow-card border-gray-800 h-full flex flex-col">
                <CardHeader className="py-4 px-6">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Connected Sources</CardTitle>
                    <span className="text-sm text-gray-400">Slack vs Documents</span>
                  </div>
                </CardHeader>
                <CardContent className="px-6 pb-6 flex-1 flex flex-col justify-between min-h-0">
                  <div className="w-full h-[320px]">
                    <ChartContainer config={{}} className="w-full h-full aspect-auto">
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Slack', value: connectedSources?.byType?.slack ?? 0 },
                            { name: 'Documents', value: connectedSources?.byType?.document ?? 0 },
                          ]}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={90}
                          stroke="transparent"
                          label
                        >
                          <Cell fill="#a78bfa" />
                          <Cell fill="#22d3ee" />
                        </Pie>
                        <ChartTooltip formatter={(value: any) => String(value)} />
                      </PieChart>
                    </ChartContainer>
                  </div>
                  <Separator className="my-1 bg-gray-800" />
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#a78bfa' }}></span>
                        <span className="text-sm">Slack</span>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-medium">{slackCount}</span>
                        <span className="text-xs text-gray-400 ml-2">{totalSources ? Math.round((slackCount / totalSources) * 100) : 0}%</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#22d3ee' }}></span>
                        <span className="text-sm">Documents</span>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-medium">{documentCount}</span>
                        <span className="text-xs text-gray-400 ml-2">{totalSources ? Math.round((documentCount / totalSources) * 100) : 0}%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </GlassPanel>
          </motion.div>

          {/* Bottom row: Recent Activity (3/4) and Active Pipelines (1/4) */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mb-8 grid grid-cols-1 xl:grid-cols-12 gap-6"
          >
            <GlassPanel className="xl:col-span-5" style={{ height: 340 }}>
              <PipelineInfoCards metrics={metrics} activePipelines={activePipelines} showProcessing={false} showConnected={false} showActive />
            </GlassPanel>
            <GlassPanel className="xl:col-span-7" style={{ height: 340 }}>
              <LiveActivityFeed compact />
            </GlassPanel>
          </motion.div>
        </main>
            <StatusBar />
      </div>
    </div>
  );
}
