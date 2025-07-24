import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import StatusBar from "@/components/layout/StatusBar";
import { PaginatedChannelTable } from "@/features/slack/PaginatedChannelTable";
import { ChannelSettingsDrawer } from "@/features/slack/ChannelSettingsDrawer";
import { AnimatePresence, motion } from "framer-motion";
import { useLocation } from "wouter";
import { fetchEmbeddedSlackChannels, fetchSystemStats, deleteSlackChannel } from "@/api/slack";
import { FaHashtag, FaComments, FaSync, FaDatabase } from "react-icons/fa";
import { useToast } from "@/hooks/use-toast";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { StatsCard, StatsCardProps } from "./StatsCard";
import { PIPELINE_STATUS } from "@/constants/pipelineStatus";
import { EmbedChannel } from "@/types";
import { formatNumber, getLastSyncTime } from "@/utils";

export interface SlackTypeData {
  message_count: number;
  api_calls: number;
};

const sharedTransition = {
  type: "spring",
  stiffness: 300,
  damping: 30,
};

// Helper functions for pipeline status management
const getActiveStatuses = () => [
  PIPELINE_STATUS.PENDING,
  PIPELINE_STATUS.ACTIVE,
  PIPELINE_STATUS.COLLECTING,
  PIPELINE_STATUS.PROCESSING,
  PIPELINE_STATUS.CHUNKING_AND_EMBEDDING,
  PIPELINE_STATUS.STORING,
  PIPELINE_STATUS.ORCHESTRATING,
];

const getInactiveStatuses = () => [
  PIPELINE_STATUS.DONE,
  PIPELINE_STATUS.FAILED,
  PIPELINE_STATUS.ARCHIVED,
  PIPELINE_STATUS.PAUSED
];

const isChannelActivelyProcessing = (channel: EmbedChannel) => {
  return getActiveStatuses().includes(channel.status as any);
};

const isChannelInactive = (channel: EmbedChannel) => {
  return getInactiveStatuses().includes(channel.status as any);
};

export default function SlackIntegration() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedChannels, setSelectedChannels] = useState<string[]>([]);
  const [settingsChannel, setSettingsChannel] = useState<EmbedChannel | null>(null);
  const [deletingChannelId, setDeletingChannelId] = useState<string | null>(null);
  const [channelToDelete, setChannelToDelete] = useState<EmbedChannel | null>(null);
  const [activeEmbedding, setActiveEmbedding] = useState<Set<string>>(new Set());
  const [, navigate] = useLocation();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Check if there are any channels in progress or being embedded
  const hasActiveOperations = (channels: EmbedChannel[] | undefined) => {
    if (!channels || !Array.isArray(channels)) return false;
    
    return channels.some(channel =>
      isChannelActivelyProcessing(channel) ||
      activeEmbedding.has(channel.channel_id)
    );
  };

  const { data: embedChannels = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ["embeddedSlackChannels"],
    queryFn: fetchEmbeddedSlackChannels,
    staleTime: 15 * 1000, // Fresh data for 15 seconds
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    // Smart polling - poll every 5 seconds when there are active pipeline operations
    refetchInterval: (query) => {
      const data = query.state.data as EmbedChannel[] | undefined;
      const hasActive = hasActiveOperations(data) || activeEmbedding.size > 0;
      
      // Log the active channels for debugging
      if (hasActive && data) {
        const activeChannels = data.filter(isChannelActivelyProcessing);
        console.log(`Live tracking enabled: ${activeChannels.length} channels actively processing`, 
                   activeChannels.map(c => `${c.name}: ${c.status}`));
      }
      
      return hasActive ? 5000 : false;
    },
  });

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ["embeddedSlackChannelsStats"],
    queryFn: fetchSystemStats,
    staleTime: 5 * 1000, // Fresh data for 5 seconds
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchInterval: 10000, // Poll every 10 seconds as baseline
  });

  // Effect to trigger additional stats refresh when channels change or embedding state changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      refetchStats();
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [embedChannels.length, activeEmbedding.size, refetchStats]);

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteSlackChannel,
    onMutate: (channelId) => {
      // Set loading state
      setDeletingChannelId(channelId);
    },
    onSuccess: (data, channelId) => {
      // Clear loading state
      setDeletingChannelId(null);
      // Invalidate and refetch the channels list
      queryClient.invalidateQueries({ queryKey: ["embeddedSlackChannels"] });
      queryClient.invalidateQueries({ queryKey: ["embeddedSlackChannelsStats"] });

      const embeddingsDeleted = data.result?.qdrant_embeddings_deleted || 0;
      const pipelineRecordsDeleted = data.result?.mongo_pipelines_deleted || 0;

      toast({
        title: "✅ Channel Deleted Successfully",
        description: `Removed ${embeddingsDeleted} embeddings and ${pipelineRecordsDeleted} pipeline records from storage.`,
        variant: "default",
      });
    },
    onError: (error: any, channelId) => {
      // Clear loading state
      setDeletingChannelId(null);
      console.error('Delete failed:', error);

      toast({
        title: "❌ Deletion Failed",
        description: `Unable to delete channel: ${error.response?.data?.error || error.message}`,
        variant: "destructive",
      });
    },
  });

  const handleSave = (values: Record<string, string | boolean>) => {
    setSettingsChannel(null);
  };

  const handleDeleteChannel = (channel: EmbedChannel) => {
    setChannelToDelete(channel);
  };

  const confirmDeleteChannel = () => {
    if (channelToDelete) {
      deleteMutation.mutate(channelToDelete.channel_id);
      setChannelToDelete(null);
    }
  };

  // Track embedding operations
  const trackEmbeddingStart = (channelIds: string[]) => {
    setActiveEmbedding(prev => {
      const newSet = new Set(prev);
      channelIds.forEach(id => newSet.add(id));
      return newSet;
    });

    // Immediately refresh stats when embedding starts
    refetchStats();

    // Show optimistic toast
    toast({
      title: "🚀 Embedding Started",
      description: `Processing ${channelIds.length} channel${channelIds.length > 1 ? 's' : ''}. This may take a few minutes.`,
      variant: "default",
    });
  };

  // Remove channels from active tracking when they complete
  const trackEmbeddingComplete = (channelIds: string[]) => {
    setActiveEmbedding(prev => {
      const newSet = new Set(prev);
      channelIds.forEach(id => newSet.delete(id));
      return newSet;
    });

    // Immediately refresh stats when embedding completes
    refetchStats();
  };

  // Effect to clean up completed embeddings
  useEffect(() => {
    if (Array.isArray(embedChannels) && embedChannels.length > 0 && activeEmbedding.size > 0) {
      const completedChannels: string[] = [];
      
      activeEmbedding.forEach(channelId => {
        const channel = embedChannels.find(c => c.channel_id === channelId);
        if (channel && isChannelInactive(channel)) {
          completedChannels.push(channelId);
        }
      });

      if (completedChannels.length > 0) {
        trackEmbeddingComplete(completedChannels);

        // Show completion toast
        const completedCount = completedChannels.length;
        const failedChannels = embedChannels.filter(c =>
          completedChannels.includes(c.channel_id) && c.status === PIPELINE_STATUS.FAILED
        );

        if (failedChannels.length > 0) {
          toast({
            title: "⚠️ Embedding Completed with Issues",
            description: `${completedCount - failedChannels.length} channels completed successfully, ${failedChannels.length} failed.`,
            variant: "destructive",
          });
        } else {
          toast({
            title: "✅ Embedding Completed",
            description: `Successfully processed ${completedCount} channel${completedCount > 1 ? 's' : ''}.`,
            variant: "default",
          });
        }
      }
    }
  }, [embedChannels, activeEmbedding, toast]);

  // Effect to detect if user came back from adding channels
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const newChannels = urlParams.get('newChannels');

    if (newChannels) {
      try {
        const channelIds = JSON.parse(decodeURIComponent(newChannels));
        if (Array.isArray(channelIds) && channelIds.length > 0) {
          trackEmbeddingStart(channelIds);
          // Clean up URL
          window.history.replaceState({}, '', window.location.pathname);
        }
      } catch (error) {
        console.error('Error parsing new channels from URL:', error);
      }
    }
  }, []);

  const handleRefresh = async () => {
    try {
      // Refresh both channels and stats
      await Promise.all([
        refetch(),
        refetchStats()
      ]);
      console.log('Successfully refreshed embedded channels and stats');
    } catch (error) {
      console.error('Error refreshing data:', error);
    }
  };

  const statsItems: Omit<StatsCardProps, 'delay'>[] = [
    {
      icon: FaHashtag,
      label: 'Active Channels',
      value: stats?.activeChannels || 0,
      delta: 8,
      color: 'emerald'
    },
    {
      icon: FaComments,
      label: 'Messages Processed',
      value: stats?.totalMessages || 0,
      delta: 12,
      formatValue: formatNumber,
      color: 'blue'
    },
    {
      icon: FaSync,
      label: 'Last Sync',
      value: getLastSyncTime(),
      status: 'Real-time',
      color: 'amber'
    },
    {
      icon: FaDatabase,
      label: 'Total Embeddings',
      value: stats?.totalEmbeddings || 0,
      formatValue: formatNumber,
      color: 'purple'
    }
  ];

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="Slack Integration" onToggleSidebar={() => setSidebarOpen((s) => !s)} />

        <main className="flex-1 overflow-y-auto p-4 bg-background-dark">
          <div className="w-full space-y-4">

            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground">System Statistics</h3>
              {activeEmbedding.size > 0 && (
                <div className="flex items-center space-x-2 px-3 py-1 bg-blue-500/10 border border-blue-400/20 rounded-full">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                  <span className="text-sm text-blue-400 font-medium">
                    {activeEmbedding.size} channel{activeEmbedding.size > 1 ? 's' : ''} embedding
                  </span>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {statsItems.map((item, idx) => (
                <StatsCard key={item.label} {...item} delay={idx * 0.1} />
              ))}
            </div>

            {/* Channel Table Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
            >
              {isLoading && <div className="text-muted-foreground">Loading channels…</div>}
              {isError && <div className="text-destructive">Failed to load channels: {error.message}</div>}

              {!isLoading && !isError && (
                <div className="flex gap-4 min-h-[400px] relative">
                  {/* Table Container with dynamic shift using transform instead of margin */}
                  <motion.div
                    className="flex transition-all duration-500 ease-in-out"
                    style={{
                      width: settingsChannel ? "calc(100% - 420px)" : "100%",
                    }}
                    animate={{
                      width: settingsChannel ? "calc(100% - 420px)" : "100%",
                    }}
                    transition={sharedTransition}
                  >
                    <PaginatedChannelTable
                      allChannels={embedChannels}
                      onSettingsClick={setSettingsChannel}
                      onDeleteClick={handleDeleteChannel}
                      onRefresh={handleRefresh}
                      deletingChannelId={deletingChannelId || undefined}
                      activeEmbeddingIds={Array.from(activeEmbedding)}
                    />
                  </motion.div>

                  {/* Settings Drawer */}
                  <AnimatePresence>
                    {settingsChannel && (
                      <motion.div
                        className="absolute right-0 top-0 w-[400px] z-10"
                        initial={{ x: 400, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: 400, opacity: 0 }}
                        transition={sharedTransition}
                      >
                        <ChannelSettingsDrawer
                          channel={settingsChannel}
                          isOpen={settingsChannel !== null}
                          onClose={() => setSettingsChannel(null)}
                          onSave={handleSave}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

              )}
            </motion.div>
          </div>
        </main>
        <StatusBar />
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={channelToDelete !== null} onOpenChange={() => setChannelToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>🗑️ Delete Channel</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the channel <strong>"{channelToDelete?.name}"</strong>?
              <br /><br />
              This will permanently remove:
              <ul className="mt-2 ml-4 list-disc text-sm">
                <li>All embeddings from vector storage</li>
                <li>All messages and chunks from database</li>
                <li>Channel configuration and settings</li>
              </ul>
              <br />
              <strong>This action cannot be undone.</strong>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteChannel}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Channel
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};