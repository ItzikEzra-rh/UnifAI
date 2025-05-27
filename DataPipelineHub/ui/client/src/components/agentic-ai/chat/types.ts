export interface Message {
    id: string;
    content: string;
    sender: 'user' | 'ai';
    timestamp: Date;
    streamLogs?: StreamLogEntry[];
    finalAnswer?: string;
  }
  
  export interface StreamLogEntry {
    nodeId: string;
    nodeName: string;
    message: string;
    status: 'processing' | 'complete' | 'error';
    isExpanded?: boolean;
  }