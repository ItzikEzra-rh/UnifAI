export interface Pipeline {
  id: string;
  name: string;
  status: 'processing' | 'waiting' | 'paused' | 'completed' | 'error';
  progress: number;
  source: DataSourceType;
  projectId: string;
}

export interface DataSource {
  id: string;
  name: string;
  type: DataSourceType;
  status: 'connected' | 'disconnected' | 'error';
  lastSync?: string;
}

export type DataSourceType = 'jira' | 'slack' | 'document' | 'github';

export interface ActivityLog {
  id: string;
  type: 'success' | 'error' | 'info';
  title: string;
  description: string;
  time: string;
  projectId: string;
  sourceType: DataSourceType;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'viewer';
  avatar?: string;
}

export interface ProjectStats {
  totalDocuments: number;
  processedDocuments: number;
  vectorCount: number;
  sourceDistribution: {
    [key in DataSourceType]?: {
      count: number;
      percentage: number;
    };
  };
}

export interface Channel {
  channel_name: string;
  channel_id: string;
  is_private: boolean;
}

export interface EmbedChannel {
  name: string;
  messages: string;
  lastSync: string;
  status: "ACTIVE" | "PAUSED" | "ARCHIVED" | "DONE" | "FAILED";
  frequency: string;
  channel_id: string;
  created: string;
  is_private: boolean;
}
