// Backend message format
export interface BackendChatMessage {
  content: string;
  role: "user" | "assistant";
}

// Shared ChatSession interface used across components
export interface ChatSession {
  id: string;
  blueprintId: string;
  title: string;
  lastActive: string;
  timestamp: Date;
  preview: string;
  messages: BackendChatMessage[];
  blueprintExists: boolean;
  fromSharedLink?: boolean;
  isSharingDisabled?: boolean; // Track if sharing is disabled for this session
}

// Types for the API response
export interface ChatSessionData {
  metadata: Record<string, any>;
  blueprint_id: string;
  session_id: string;
  started_at: string;
  blueprint_exists: boolean;
}

export interface SessionStateData {
  final_output: string;
  messages: BackendChatMessage[];
}