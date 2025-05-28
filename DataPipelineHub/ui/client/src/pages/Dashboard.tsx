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
import PipelineVisualizer from "@/components/dashboard/PipelineVisualizer";
import ProjectCard from "@/components/dashboard/ProjectCard";
import ActivityFeed from "@/components/dashboard/ActivityFeed";
import DataSourceStats from "@/components/dashboard/DataSourceStats";

export default function Dashboard() {
  const { projects } = useProject();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Activity feed data
  const activities = [
    {
      id: '1',
      type: 'success' as const,
      title: 'Jira pipeline processing completed',
      time: '10 min ago',
      description: 'Successfully processed 230 Jira tickets from the Engineering board.',
      project: { name: 'Test Autmation Generator', color: 'primary' },
      source: 'Jira'
    },
    {
      id: '2',
      type: 'error' as const,
      title: 'Slack connection error',
      time: '1 hour ago',
      description: 'API rate limit exceeded when processing #general channel. Retrying in 15 minutes.',
      project: { name: 'AI Assistant', color: 'secondary' },
      source: 'Slack'
    },
    {
      id: '3',
      type: 'info' as const,
      title: 'Document processing started',
      time: '3 hours ago',
      description: 'Started processing 28 new PDF documents from shared drive.',
      project: { name: 'Data Warehouse', color: 'accent' },
      source: 'Documents'
    }
  ];
  
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
        <main className="flex-1 overflow-y-auto p-6 bg-background-dark">
          {/* Dashboard Summary Cards */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
          >
            <StatusCard 
              title="Active Pipelines" 
              value="12" 
              icon={<FaStream />} 
              iconBgColor="bg-primary"
              statusItems={[
                { label: "Processing", value: "4 pipelines", color: "success" },
                { label: "Waiting", value: "7 pipelines", color: "secondary" },
                { label: "Paused", value: "1 pipeline", color: "accent" }
              ]}
            />
            
            <StatusCard 
              title="Connected Sources" 
              value="5 / 8" 
              icon={<FaPlug />} 
              iconBgColor="bg-secondary"
              statusItems={[
                { label: "Jira", value: "Connected", color: "success" },
                { label: "Slack", value: "Connected", color: "success" },
                { label: "GitHub", value: "Disconnected", color: "gray-600" }
              ]}
            />
            
            <StatusCard 
              title="Processing Stats" 
              value="98.2%" 
              icon={<FaChartPie />} 
              iconBgColor="bg-accent"
              progressItems={[
                { label: "Successful embeddings", value: "15.2K", percentage: 95, color: "bg-gradient-to-r from-primary to-secondary" },
                { label: "Processing speed", value: "132/min", percentage: 78, color: "bg-secondary" }
              ]}
            />
          </motion.div>

          {/* Pipeline Activity Visualization */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-8"
          >
            <PipelineVisualizer title="Pipeline Activity" />
          </motion.div>

          {/* Projects Row */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mb-8"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading font-semibold text-lg">Your Projects</h2>
              <button className="px-3 py-1 bg-background-card hover:bg-opacity-80 rounded text-sm font-medium text-gray-400 hover:text-white transition-colors flex items-center">
                <span>View All</span>
                <FaChevronRight className="ml-2 text-xs" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project) => (
                <ProjectCard
                  key={project.id}
                  name={project.name}
                  shortName={project.shortName}
                  icon={project.icon}
                  updatedTime={project.updatedTime}
                  processingPercentage={project.processingPercentage}
                  color={project.color}
                  isActive={project.isActive}
                  sources={project.sources}
                  documents={project.documents}
                />
              ))}
            </div>
          </motion.div>

          {/* Recent Activity & Data Source Stats */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-6"
          >
            {/* Recent Activity */}
            <div className="lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-heading font-semibold text-lg">Recent Activity</h2>
                <button className="px-3 py-1 bg-background-card hover:bg-opacity-80 rounded text-sm font-medium text-gray-400 hover:text-white transition-colors">
                  View All
                </button>
              </div>
              
              <ActivityFeed activities={activities} />
            </div>
            
            {/* Data Source Stats */}
            <div className="lg:col-span-1">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-heading font-semibold text-lg">Data Source Analytics</h2>
                <button className="text-gray-400 hover:text-white">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                  </svg>
                </button>
              </div>
              
              <DataSourceStats 
                totalVectors={dataSourceStats.totalVectors}
                stats={dataSourceStats.stats}
              />
            </div>
          </motion.div>
        </main>
        
        {/* Status Bar */}
        <StatusBar />
      </div>
    </div>
  );
}
