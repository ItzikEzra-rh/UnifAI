import { formatDate } from '@/features/helpers';
import { api } from '@/lib/queryClient';
import type { Channel, EmbedChannel } from '@/types';
import { timeAgo } from '@/utils';
export interface SystemStats {
  id: number;
  totalChannels: number;
  activeChannels: number;
  totalMessages: number;
  apiCallsCount: number;
  lastSyncAt: string | null;
  totalEmbeddings: number;
  updatedAt: string;
};

export async function fetchAvailableSlackChannels(
  types: string
): Promise<Channel[]> {
  const { data } = await api.get<{
    channels: Channel[];
  }>('slack/available.slack.channels.get', {
    params: { types },
  });

  return data.channels.map((c) => ({
    channel_name: c.channel_name,
    channel_id:   c.channel_id,
    is_private:   c.is_private,
  }));
};

export async function submitSlackChannels(
  channels: Channel[]
): Promise<{ status: string }> {
  const { data } = await api.put<{ status: string }>(
    'pipelines/embed',
    { data: channels,
      type: 'slack' }
  );
  return data;
};

export async function fetchEmbeddedSlackChannels(): Promise<EmbedChannel[]> {
  const { data } = await api.get<any[]>("slack/embed.channels");
  return data.map((item) => ({
    name: item.source_name || '', 
    messages: String(item.pipeline_stats?.documents_retrieved || 0),
    lastSync: timeAgo(item.last_sync_at),
    status: item.status || 'PENDING',
    frequency: "", // No field provided, fallback to empty
    channel_id: item.source_id || '',
    created: formatDate(item.created_at || ''),
    is_private: item.type_data?.is_private || false,
  }));
};

export async function deleteSlackChannel(channelId: string): Promise<any> {
  const { data } = await api.delete(`slack/embed.channels/${channelId}`);
  return data;
};

export async function fetchSystemStats(): Promise<SystemStats> {
  const response = await api.get("/slack/stats");
  return response.data;
};