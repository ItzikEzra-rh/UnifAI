import { Card, CardContent } from "@/components/ui/card";
import { motion } from "framer-motion";
import { Activity, Database, TrendingUp, FileText, MessageSquare, Bug, Slack as SlackIcon, Clock, Menu, PieChart, Plug } from "lucide-react";
import type { PipelineMetrics, ActivePipeline } from "@/api/pipelines";

interface PipelineInfoCardsProps {
  metrics?: PipelineMetrics;
  activePipelines?: ActivePipeline[];
  showProcessing?: boolean;
  showConnected?: boolean;
  showActive?: boolean;
  showLastSync?: boolean;
}

export function PipelineInfoCards({ metrics, activePipelines = [], showProcessing = true, showConnected = true, showActive = true, showLastSync = false }: PipelineInfoCardsProps) {
  const ProcessingStatsCard = () => (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
      <Card className="rounded-xl border-0">
        <div className="relative p-4 border-b border-border">
          <div className="absolute top-2 right-4 w-8 h-8 rounded-lg bg-primary text-white flex items-center justify-center shadow-lg/30 shadow-primary/40">
            <Menu className="w-4 h-4" />
          </div>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <TrendingUp className="text-primary mr-3 h-5 w-5" />
            Processing Stats
          </h3>
        </div>
        <CardContent className="p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide">Success Rate</p>
              <p className="text-xl font-bold" style={{ color: 'hsl(var(--success))' }}>{(metrics?.successRate ?? 0).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide">Active Pipelines</p>
              <p className="text-xl font-bold text-white">{metrics?.activePipelines || 0}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide">Total Pipelines</p>
              <p className="text-xl font-bold text-white">{metrics?.totalPipelines || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );

  const ConnectedSourcesCard = () => {
    const sourceTypes = ["slack", "document"] as const;
    const getSourceIcon = (type: string) => {
      switch (type) {
        case "slack":
          return <MessageSquare className="h-4 w-4" />;
        case "document":
          return <FileText className="h-4 w-4" />;
        default:
          return <Database className="h-4 w-4" />;
      }
    };

    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
        <Card className="rounded-xl border-0">
          <div className="relative p-4 border-b border-border">
            <div className="absolute top-2 right-4 w-8 h-8 rounded-lg bg-gray-800 text-white flex items-center justify-center shadow-lg/20">
              <PieChart className="w-4 h-4" />
            </div>
            <h3 className="text-lg font-semibold text-white flex items-center">
              <Database className="text-primary mr-3 h-5 w-5" />
              Connected Sources
            </h3>
          </div>
          <CardContent className="p-4 space-y-3">
            {sourceTypes.map((type) => {
              const count = activePipelines.filter((p) => p.source_type === (type as any) || (p as any).type === type).length;
              const isActive = count > 0;
              return (
                <div key={type} className="flex items-center justify-between p-2 rounded-lg bg-gray-900 bg-opacity-30">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isActive ? "bg-primary bg-opacity-20 text-primary" : "bg-gray-700 text-gray-400"
                    }`}>
                      {getSourceIcon(type)}
                    </div>
                    <span className="text-white font-medium capitalize">{type}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-400">{count} active</span>
                    <div className={`w-2 h-2 rounded-full ${isActive ? "animate-pulse" : "bg-gray-600"}`} style={{ backgroundColor: 'hsl(var(--success))' }}></div>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  const LastSyncCard = () => {
    // Placeholder stats until backend provides real values
    const avgMinutes = 18; // average minutes since last sync
    const mostStale = "1h 42m";
    const updatedAgo = "2m ago";
    const staleChannels = 3;


    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.25 }} className="h-full">
        <Card className="rounded-xl border-0 h-full min-h-[200px]">
          <div className="relative p-4 border-b border-border">
            <div className="absolute top-2 right-4 w-8 h-8 rounded-lg bg-gray-800 text-white flex items-center justify-center shadow-lg/20">
              <Plug className="w-4 h-4" />
            </div>
            <h3 className="text-lg font-semibold text-white flex items-center">
              <Clock className="text-primary mr-3 h-5 w-5" />
              Data Freshness
            </h3>
          </div>
          <CardContent className="p-4">
            <div className="grid grid-cols-3 gap-4 items-end">
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Avg Last Sync</p>
                <p className={`text-2xl font-bold `}>{avgMinutes}m</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Most Stale</p>
                <p className="text-xl font-bold text-white">{mostStale}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400 uppercase tracking-wide">Stale Channels</p>
                <p className="text-xl font-bold text-white">{staleChannels}</p>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-400">Updated {updatedAgo}</div>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  const ActivePipelinesCard = () => {
    const activeCount = activePipelines.filter(
      (p) => p.status === "PROCESSING" || p.status === "COLLECTING" || p.status === "CHUNKING_AND_EMBEDDING"
    ).length;

    const getStatusBadge = (status: string) => {
      switch (status) {
        case 'Done':
        case 'complete':
          return { color: 'badge-slack-green', label: status === 'Done' ? 'Success' : 'Complete' };
        case 'PROCESSING':
        case 'COLLECTING':
        case 'CHUNKING_AND_EMBEDDING':
          return { color: 'badge-slack-blue', label: 'Processing' };
        case 'FAILED':
        case 'error':
          return { color: 'badge-slack-red', label: 'Error' };
        default:
          return { color: 'badge-slack-purple', label: status };
      }
    };

    const getActivityIcon = (type: string) => {
      switch (type) {
        case 'slack':
          return <SlackIcon className="text-white text-sm" />;
        case 'document':
          return <FileText className="text-white text-sm" />;
        default:
          return <MessageSquare className="text-white text-sm" />;
      }
    };

    const getActivityColor = (_type: string) => 'bg-primary';

    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
        <Card className="rounded-xl border-0">
          <div className="p-4 border-b border-border">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <Activity className="text-primary mr-3 h-5 w-5" />
              Active Pipelines
              <div className="ml-2 flex items-center">
                <div className="w-2 h-2 bg-secondary rounded-full animate-pulse mr-1"></div>
                <span className="text-secondary text-xs font-medium">{activeCount}</span>
              </div>
            </h3>
          </div>
          <CardContent className="p-4">
            {activePipelines.length === 0 ? (
              <div className="text-center text-gray-400 py-4">No active pipelines</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-80 overflow-y-auto overflow-x-hidden">
                {activePipelines.map((pipeline) => {
                  const statusBadge = getStatusBadge(pipeline.status);
                  const borderColor = pipeline.status === 'FAILED' ? 'border-red-900' : 'border-gray-700';
                  return (
                    <motion.div
                      key={pipeline.id}
                      initial={{ opacity: 0, y: 12, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -12, scale: 0.98 }}
                      transition={{ type: "spring", stiffness: 380, damping: 26, mass: 0.8 }}
                      className={`w-full min-w-0 h-full p-4 bg-gray-900 bg-opacity-30 rounded-lg flex flex-col justify-between`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 ${getActivityColor(pipeline.source_type)} rounded-full flex items-center justify-center`}>
                            {getActivityIcon(pipeline.source_type)}
                          </div>
                          <span className="text-white font-medium text-sm break-words" title={pipeline.source_name}>
                            {pipeline.source_name}
                          </span>
                        </div>
                        <span className="text-gray-400 text-xs ml-3 whitespace-nowrap">
                          {(pipeline.pipeline_stats?.documents_retrieved || 0)} docs
                        </span>
                      </div>
                      <div className="flex items-center mt-3 gap-2">
                        <span className={`px-2 py-1 ${statusBadge.color} text-xs rounded`}>
                          {statusBadge.label}
                        </span>
                        <span className="px-2 py-1 bg-gray-800 text-gray-300 text-xs rounded capitalize">
                          {pipeline.source_type}
                        </span>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      {showProcessing && <ProcessingStatsCard />}
      {showConnected && <ConnectedSourcesCard />}
      {showLastSync && <LastSyncCard />}
      {showActive && <ActivePipelinesCard />}
    </div>
  );
}


