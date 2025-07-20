import { PipelineStatus } from '@/constants/pipelineStatus';

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
  status: PipelineStatus;
  frequency: string;
  channel_id: string;
  created: string;
  is_private: boolean;
}
export interface Document {
  last_pipeline_id: string;
  source_name: string;
  status: PipelineStatus;
  created_at: string;
  file_type: string;
  chunks_generated: number;
  type_data: {
    doc_path: string;
    page_count: number;
    full_text: string;
    file_size: string;
  };
  upload_by: string;
  last_updated: string;
  stats?: {
    total_tokens?: number;
    avg_chunk_size?: number;
    images_extracted?: number;
    tables_extracted?: number;
    embeddings_created?: number;
    api_calls?: number;
    processing_time?: number;
  };
}
