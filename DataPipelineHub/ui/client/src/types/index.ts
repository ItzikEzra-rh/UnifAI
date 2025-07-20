// Constants for string literal unions
export const PIPELINE_STATUS = {
  PROCESSING: 'processing',
  WAITING: 'waiting',
  PAUSED: 'paused',
  COMPLETED: 'completed',
  ERROR: 'error'
} as const;

export const DATA_SOURCE_STATUS = {
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
} as const;

export const DATA_SOURCE_TYPE = {
  JIRA: 'jira',
  SLACK: 'slack',
  DOCUMENT: 'document',
  GITHUB: 'github'
} as const;

export const ACTIVITY_LOG_TYPE = {
  SUCCESS: 'success',
  ERROR: 'error',
  INFO: 'info'
} as const;

export const USER_ROLE = {
  ADMIN: 'admin',
  USER: 'user',
  VIEWER: 'viewer'
} as const;

export const EMBED_CHANNEL_STATUS = {
  ACTIVE: 'ACTIVE',
  PAUSED: 'PAUSED',
  ARCHIVED: 'ARCHIVED',
  DONE: 'DONE',
  FAILED: 'FAILED',
  CHUNKING_AND_EMBEDDING: 'CHUNKING_AND_EMBEDDING',
  STORING: 'STORING',
  COLLECTING: 'COLLECTING',
  PROCESSING: 'PROCESSING',
  ORCHESTRATING: 'ORCHESTRATING'
} as const;

// Type definitions
export type PipelineStatus = typeof PIPELINE_STATUS[keyof typeof PIPELINE_STATUS];
export type DataSourceStatus = typeof DATA_SOURCE_STATUS[keyof typeof DATA_SOURCE_STATUS];
export type DataSourceType = typeof DATA_SOURCE_TYPE[keyof typeof DATA_SOURCE_TYPE];
export type ActivityLogType = typeof ACTIVITY_LOG_TYPE[keyof typeof ACTIVITY_LOG_TYPE];
export type UserRole = typeof USER_ROLE[keyof typeof USER_ROLE];
export type EmbedChannelStatus = typeof EMBED_CHANNEL_STATUS[keyof typeof EMBED_CHANNEL_STATUS];

// Interfaces
export interface Pipeline {
  id: string;
  name: string;
  status: PipelineStatus;
  progress: number;
  source: DataSourceType;
  projectId: string;
}

export interface DataSource {
  id: string;
  name: string;
  type: DataSourceType;
  status: DataSourceStatus;
  lastSync?: string;
}

export interface ActivityLog {
  id: string;
  type: ActivityLogType;
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
  role: UserRole;
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
  status: EmbedChannelStatus;
  frequency: string;
  channel_id: string;
  created: string;
  is_private: boolean;
}
