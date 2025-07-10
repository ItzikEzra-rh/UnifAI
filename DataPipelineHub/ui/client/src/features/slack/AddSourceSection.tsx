import React, { FC, useState, useMemo, useCallback, forwardRef, useImperativeHandle, useEffect, useRef } from 'react';
import { useInfiniteQuery, useQuery, useQueryClient } from '@tanstack/react-query';
import { FaSearch, FaSpinner } from 'react-icons/fa';
import { HiOutlineLockClosed } from 'react-icons/hi';

import { fetchAvailableSlackChannels, fetchEmbeddedSlackChannels } from '@/api/slack';
import type { EmbedChannel, Channel } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// ── Pagination Constants ──────────────────────────────────────────────
const CHANNELS_PER_PAGE = 50;

// ── Scope Constants ────────────────────────────────────────────────────
export const SCOPE = {
  ALL: 'all' as const,
  PUBLIC: 'public' as const,
  PRIVATE: 'private' as const,
};
export type Scope = typeof SCOPE[keyof typeof SCOPE];

// ── Channel Type Constants ─────────────────────────────────────────────
export const CHANNEL_TYPE = {
  PUBLIC: 'public_channel' as const,
  PRIVATE: 'private_channel' as const,
};
export type ChannelType = typeof CHANNEL_TYPE[keyof typeof CHANNEL_TYPE];
export const ALL_CHANNEL_TYPES = `${CHANNEL_TYPE.PUBLIC},${CHANNEL_TYPE.PRIVATE}` as const;

// ── Cache Key ─────────────────────────────────────────────────────────
const CACHE_KEY = 'slackChannels';

// ── Scope Options ──────────────────────────────────────────────────────
const scopeOptions: { label: string; value: Scope }[] = [
  { label: 'All', value: SCOPE.ALL },
  { label: 'Public', value: SCOPE.PUBLIC },
  { label: 'Private', value: SCOPE.PRIVATE },
];

// ── Pagination Response Interface ──────────────────────────────────────
export interface PaginatedChannelsResponse {
  channels: Channel[];
  nextCursor?: string;
  hasMore: boolean;
  total?: number;
}

export interface AddSourceSectionHandle {
  getSelectedChannels: () => Promise<Channel[]>;
}

export interface AddSourceSectionProps {
  onSave?: () => void;
  onCancel?: () => void;
  isSubmitting?: boolean;
}

// Helper functions for unique channel identification
const getChannelUniqueId = (channel: Channel) => `${channel.channel_id}_${channel.is_private ? 'private' : 'public'}`;
const parseChannelUniqueId = (uniqueId: string) => {
  const parts = uniqueId.split('_');
  return {
    channel_id: parts.slice(0, -1).join('_'), // Handle channel_ids that might contain underscores
    is_private: parts[parts.length - 1] === 'private'
  };
};

// ── Component ──────────────────────────────────────────────────────────
const AddSourceSection = forwardRef<AddSourceSectionHandle, AddSourceSectionProps>(({ onSave, onCancel, isSubmitting }, ref) => {
  const queryClient = useQueryClient();
  const [scope, setScope] = useState<Scope>(SCOPE.ALL);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedChannels, setSelectedChannels] = useState<string[]>([]);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Slack API `types` param mapping
  const typesParam = useMemo<ChannelType | typeof ALL_CHANNEL_TYPES>(() => {
    if (scope === SCOPE.PUBLIC) return CHANNEL_TYPE.PUBLIC;
    if (scope === SCOPE.PRIVATE) return CHANNEL_TYPE.PRIVATE;
    return ALL_CHANNEL_TYPES;
  }, [scope]);

  // Reset selected channels when scope changes
  useEffect(() => {
    setSelectedChannels([]);
  }, [scope]);

  // Infinite query for channels
  const {
    data: channelsData,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery<PaginatedChannelsResponse, Error>({
    queryKey: [CACHE_KEY, typesParam],
    queryFn: async ({ pageParam = undefined }) => {
      if (scope === SCOPE.ALL) {
        // For ALL scope, we need to fetch both public and private channels
        const [pubResponse, privResponse] = await Promise.all([
          fetchAvailableSlackChannels(CHANNEL_TYPE.PUBLIC, {
            cursor: pageParam as string,
            limit: Math.ceil(CHANNELS_PER_PAGE / 2),
          }),
          fetchAvailableSlackChannels(CHANNEL_TYPE.PRIVATE, {
            cursor: pageParam as string,
            limit: Math.ceil(CHANNELS_PER_PAGE / 2),
          }),
        ]);

        // Merge and deduplicate channels
        const mergedChannels = [...pubResponse.channels, ...privResponse.channels];
        const uniqueChannels = Array.from(
          new Map(mergedChannels.map(c => [c.channel_id, c])).values()
        );

        return {
          channels: uniqueChannels,
          nextCursor: pubResponse.nextCursor || privResponse.nextCursor,
          hasMore: pubResponse.hasMore || privResponse.hasMore,
          total: (pubResponse.total || 0) + (privResponse.total || 0),
        };
      }

      return fetchAvailableSlackChannels(typesParam as ChannelType, {
        cursor: pageParam as string,
        limit: CHANNELS_PER_PAGE,
      });
    },
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    staleTime: 5 * 60 * 1000,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    initialPageParam: undefined,
  });

  // Flatten all pages into a single array
  const channels = useMemo(() => {
    if (!channelsData?.pages) return [];
    return channelsData.pages.flatMap(page => page.channels);
  }, [channelsData]);

  // Get total count from the first page
  const totalChannels = useMemo(() => {
    return channelsData?.pages?.[0]?.total || 0;
  }, [channelsData]);

  // Get embedded channels to check for already embedded ones
  const { data: embedChannels = [] } = useQuery<EmbedChannel[], Error>({
    queryKey: ["embeddedSlackChannels"],
    queryFn: fetchEmbeddedSlackChannels,
    staleTime: 30 * 1000, // Reduce stale time for more frequent updates
    refetchOnMount: true, // Always refetch when component mounts
    refetchOnWindowFocus: true, // Refetch when user comes back to the page
  });

  const getSelectedChannels = useCallback(() => {
    return channels.filter(c => selectedChannels.includes(c.channel_name));
  }, [channels, selectedChannels]);

  useImperativeHandle(ref, () => ({
    getSelectedChannels,
  }));

  // Check if a channel is already embedded
  const isChannelEmbedded = useCallback((channel: Channel) => {
    return embedChannels.some(embedded => embedded.name === channel.channel_name);
  }, [embedChannels]);

  // Filter channels by search term
  const filteredChannels = useMemo(
    () => channels.filter(c => c.channel_name.toLowerCase().includes(searchTerm.toLowerCase())),
    [channels, searchTerm]
  );

  // Toggle a channel selection
  const handleToggleChannel = useCallback((name: string) => {
    if (isChannelEmbedded(name)) {
      return;
    }
    
    const uniqueId = getChannelUniqueId(channel);
    setSelectedChannels(prev =>
      prev.includes(uniqueId) ? prev.filter(n => n !== uniqueId) : [...prev, uniqueId]
    );
  }, [isChannelEmbedded]);

  // Select all or clear all (excluding embedded channels)
  const selectableChannels = useMemo(() => 
    filteredChannels.filter(c => !isChannelEmbedded(c)), 
    [filteredChannels, isChannelEmbedded]
  );
  const selectableChannelIds = useMemo(() => 
    selectableChannels.map(c => getChannelUniqueId(c)), 
    [selectableChannels]
  );
  const allSelected = selectableChannelIds.length > 0 && selectableChannelIds.every(id => selectedChannels.includes(id));
  const handleSelectAll = useCallback(() => {
    setSelectedChannels(prev => (allSelected ? [] : Array.from(new Set([...prev, ...allNames]))));
  }, [allNames, allSelected]);

  // Infinite scroll handler
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current || !hasNextPage || isFetchingNextPage) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const scrolledToBottom = scrollHeight - scrollTop - clientHeight < 100; // 100px threshold

    if (scrolledToBottom) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Add scroll listener
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  // Compute counts for display
  const counts: Record<Scope, number> = useMemo(() => {
    if (scope === SCOPE.ALL) {
      return {
        [SCOPE.ALL]: totalChannels,
        [SCOPE.PUBLIC]: 0,
        [SCOPE.PRIVATE]: 0,
      };
    }

    return {
      [SCOPE.ALL]: 0,
      [SCOPE.PUBLIC]: scope === SCOPE.PUBLIC ? totalChannels : 0,
      [SCOPE.PRIVATE]: scope === SCOPE.PRIVATE ? totalChannels : 0,
    };
  }, [scope, totalChannels]);

  return (
    <Card className="bg-background-card shadow-card border-gray-800">
      <CardContent className="p-4 space-y-4">
        <h3 className="text-lg font-semibold">Channel Selection</h3>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex bg-muted rounded-lg p-1">
              {scopeOptions.map(({ label, value }) => (
                <button
                  key={value}
                  onClick={() => setScope(value)}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    scope === value
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground hover:bg-background'
                  }`}
                >
                  {`${label} ${counts[value] > 0 ? `(${counts[value]})` : ''}`}
                </button>
              ))}
            </div>
            <div className="relative w-64">
              {!searchTerm && (
                <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm pointer-events-none">
                  Search Channels
                </div>
              )}
              <Input 
                id="channel-search" 
                value={searchTerm} 
                onChange={e => setSearchTerm(e.target.value)} 
                placeholder="" 
                className={`pr-10 bg-input border-border ${searchTerm ? 'pl-3' : 'pl-28'}`}
                style={{ color: 'hsl(var(--input-foreground))' }}
              />
              <FaSearch className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            </div>
          </div>
          <div className="flex space-x-3">
            <Button 
              variant="outline" 
              onClick={onCancel}
              className="border-border text-foreground hover:bg-muted"
            >
              Cancel
            </Button>
            <Button
              onClick={onSave}
              disabled={isSubmitting}
              className="btn-animated bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {isSubmitting && (
                <FaSpinner className="animate-spin text-current mr-2" />
              )}
              <span>
                {isSubmitting 
                  ? 'Submitting…' 
                  : `Add Channel${selectedChannels.length !== 1 ? 's' : ''} (${selectedChannels.length})`
                }
              </span>
            </Button>
          </div>
        </div>

        <div className="text-sm text-gray-400">
          Showing {filteredChannels.length} of {channels.length} loaded channels
          {totalChannels > 0 && channels.length < totalChannels && (
            <span> ({totalChannels} total)</span>
          )}
        </div>

        <div 
          ref={scrollContainerRef}
          className="border border-gray-800 rounded-md h-48 overflow-y-auto bg-background-dark"
        >
          {isLoading && channels.length === 0 && (
            <div className="p-4 text-center text-gray-400">
              <FaSpinner className="animate-spin inline mr-2" />
              Loading channels...
            </div>
          )}
          
          {isError && (
            <div className="p-4 text-center text-red-500">{error?.message}</div>
          )}
          
          {!isLoading && !isError && filteredChannels.length === 0 && channels.length > 0 && (
            <div className="p-4 text-center text-gray-500">No channels found matching your search</div>
          )}
          
          {!isLoading && !isError && channels.length === 0 && (
            <div className="p-4 text-center text-gray-500">No channels available</div>
          )}

          {filteredChannels.map(c => {
            const isEmbedded = isChannelEmbedded(c);
            const uniqueId = getChannelUniqueId(c);
            return (
              <div 
                key={uniqueId} 
                className={`flex items-center justify-between p-3 border-b border-gray-800 ${
                  isEmbedded ? 'opacity-60 cursor-not-allowed' : 'hover:bg-background-surface cursor-pointer'
                }`}
                onClick={() => !isEmbedded && handleToggleChannel(c)}
              >
                <div className="flex items-center">
                  <span className="text-gray-400 mr-2">{c.is_private ? <HiOutlineLockClosed className="inline" /> : '#'}</span>
                  <span>{c.channel_name}</span>
                  {c.is_private && <Badge className="ml-2 bg-secondary bg-opacity-20 text-gray-400">Private</Badge>}
                  {!c.is_private && <Badge className="ml-2 bg-secondary bg-opacity-20 text-gray-400">Public</Badge>}
                  {isEmbedded && <Badge className="ml-2 bg-green-500/20 text-green-400 border border-green-400/30">Embedded</Badge>}
                </div>
                <Switch 
                  checked={isEmbedded || selectedChannels.includes(uniqueId)} 
                  disabled={isEmbedded}
                  onCheckedChange={() => handleToggleChannel(c)} 
                />
              </div>
            );
          })}

          {/* Loading indicator for infinite scroll */}
          {isFetchingNextPage && (
            <div className="p-4 text-center text-gray-400">
              <FaSpinner className="animate-spin inline mr-2" />
              Loading more channels...
            </div>
          )}

          {/* Load more button as fallback */}
          {hasNextPage && !isFetchingNextPage && (
            <div className="p-4 text-center">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => fetchNextPage()}
                className="w-full"
              >
                Load More Channels
              </Button>
            </div>
          )}
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm">{selectedChannels.length} channel{selectedChannels.length !== 1 && 's'} selected</span>
          <Button variant="outline" size="sm" onClick={handleSelectAll}>
            {allSelected ? 'Clear All' : 'Select All'}
          </Button>
        </div>

        <div>
          <Label htmlFor="date-range" className="text-sm">
            Date Range
          </Label>
          <Select defaultValue="30d">
            <SelectTrigger
              id="date-range"
              className="mt-1 bg-background-dark"
            >
              <SelectValue placeholder="Select date range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="180d">Last 6 months</SelectItem>
              <SelectItem value="365d">Last year</SelectItem>
              <SelectItem value="all">All time</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-400 mt-1">
            How far back to fetch messages
          </p>
        </div>

        <div className="flex items-center justify-between pt-1">
          <div>
            <Label htmlFor="include-threads" className="text-base">
              Include Threads
            </Label>
            <p className="text-xs text-gray-400 mt-1">
              Process conversation threads
            </p>
          </div>
          <Switch id="include-threads" defaultChecked />
        </div>

        <div className="flex items-start justify-between opacity-50 cursor-not-allowed">
          <div>
            <div className="flex items-center space-x-2">
              <Label htmlFor="include-files" className="text-base">
                Process File Content
              </Label>
              <span className="text-xs px-2 py-0.5 rounded-full bg-primary text-white font-medium">
                Soon
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Extract text from shared files
            </p>
          </div>
          <div className="flex items-center space-x-2 pt-1">
            <Switch id="include-files" disabled />
          </div>
        </div>
      </CardContent>
    </Card>
  );
});

export default AddSourceSection;