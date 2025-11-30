import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import axios from '@/http/axiosAgentConfig';
import { ChatSession, BackendChatMessage, ChatSessionData, SessionStateData } from '@/types/session';
import { formatRelativeTimestamp } from '@/utils';
import { getPublicUsageScope } from '@/api/blueprints';

interface UsePublicChatReturn {
  sessions: ChatSession[];
  selectedSession: ChatSession | null;
  isLoading: boolean;
  isCreatingSession: boolean;
  isDeleting: boolean;
  chatHistory: BackendChatMessage[];
  runId: string | null;
  handleNewChat: () => Promise<void>;
  handleSessionSelect: (session: ChatSession) => Promise<void>;
  handleDeleteChat: (session: ChatSession, event: React.MouseEvent) => void;
  confirmDeleteChat: () => Promise<void>;
  cancelDeleteChat: () => void;
  triggerExecution: (sessionPayload: any) => Promise<string>;
  showDeleteModal: boolean;
  chatToDelete: ChatSession | null;
}

// Helper function to generate random title
const generateRandomTitle = (index: number): string => {
  const titles = ['Chat Session', 'Conversation', 'Discussion', 'Chat'];
  return `${titles[index % titles.length]} ${index + 1}`;
};

// Helper function to get preview text from messages
const getPreviewText = (messages: BackendChatMessage[]): string => {
  if (!messages || messages.length === 0) return 'No messages yet';
  const lastMessage = messages[messages.length - 1];
  return lastMessage.content.substring(0, 50) + (lastMessage.content.length > 50 ? '...' : '');
};

export const usePublicChat = (blueprintId: string | null): UsePublicChatReturn => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<ChatSession | null>(null);
  const [chatHistory, setChatHistory] = useState<BackendChatMessage[]>([]);
  const [runId, setRunId] = useState<string | null>(null);

  // Transform API data to ChatSession format
  const transformApiDataToSessions = useCallback(
    async (apiData: ChatSessionData[]): Promise<ChatSession[]> => {
      // Transform sessions and fetch fresh public_usage_scope status for shared link sessions
      const transformedSessions = await Promise.all(
        apiData.map(async (sessionData, index) => {
          const title = sessionData.metadata?.title || generateRandomTitle(index);
          const id = sessionData.session_id;
          const sessionBlueprintId = sessionData.blueprint_id;
          const blueprintExists = sessionData.blueprint_exists;
          const fromSharedLink = sessionData.metadata?.source === 'public_link';

          // Fetch fresh public_usage_scope status for shared link sessions to ensure accuracy
          let isSharingDisabled = false;
          if (fromSharedLink && blueprintExists && sessionBlueprintId) {
            try {
              const statusResponse = await getPublicUsageScope(sessionBlueprintId);
              isSharingDisabled = statusResponse.public_usage_scope !== true;
            } catch (error) {
              // If status check fails, use the value from API response as fallback
              isSharingDisabled = !(sessionData.public_usage_scope ?? false);
            }
          }

          const timestamp = new Date(sessionData.started_at);
          const lastActive = formatRelativeTimestamp(sessionData.started_at);
          const preview = 'Click to load messages...';

          return {
            id,
            blueprintId: sessionBlueprintId,
            title: fromSharedLink ? `${title} (Shared Link)` : title,
            lastActive,
            timestamp,
            preview,
            messages: [], // Messages will be loaded separately when session is selected
            blueprintExists,
            fromSharedLink,
            isSharingDisabled,
          };
        })
      );

      return transformedSessions;
    },
    []
  );

  // Fetch session state (messages) for a specific session
  const fetchSessionState = useCallback(async (sessionId: string): Promise<SessionStateData | null> => {
    try {
      const response = await axios.get(`/sessions/session.state.get?sessionId=${sessionId}`);
      return response.data;
    } catch (err) {
      console.error('Error fetching session state:', err);
      return null;
    }
  }, []);

  // Load chat sessions for this user and blueprint
  const fetchChatSessions = useCallback(async () => {
    if (!isAuthenticated || !user || !blueprintId) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.get(`/sessions/session.user.chat.get?userId=${user.username}`);
      const allSessions: ChatSessionData[] = response.data;

      // Filter sessions for this blueprint
      const blueprintSessions = allSessions.filter(
        (session) => session.blueprint_id === blueprintId && session.blueprint_exists
      );

      // Transform to ChatSession format
      const transformedSessions = await transformApiDataToSessions(blueprintSessions);

      // Sort by timestamp (most recent first)
      transformedSessions.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

      setSessions(transformedSessions);

      // If no sessions exist, automatically create a new chat
      if (transformedSessions.length === 0 && !selectedSession && !runId) {
        // Auto-create a new chat session - do this synchronously without loading states
        try {
          const createResponse = await axios.post('/sessions/user.session.create', {
            blueprintId: blueprintId,
            userId: user.username,
            metadata: { source: 'public_link' },
          });

          const newSessionId = createResponse.data;

          // Validate that we got a session ID
          if (!newSessionId || typeof newSessionId !== 'string') {
            throw new Error('Invalid session ID received from server');
          }

          // Set runId immediately so the chat interface shows right away
          setRunId(newSessionId);
          setChatHistory([]);

          // Create a temporary session object for the new session
          const tempSession: ChatSession = {
            id: newSessionId,
            blueprintId: blueprintId,
            title: 'New Chat',
            lastActive: 'Just now',
            timestamp: new Date(),
            preview: 'New conversation',
            messages: [],
            blueprintExists: true,
            fromSharedLink: true,
          };

          // Select the new session immediately
          setSelectedSession(tempSession);

          // Refresh sessions list to get proper data (do this in background, don't wait)
          axios
            .get(`/sessions/session.user.chat.get?userId=${user.username}`)
            .then(async (refreshResponse) => {
              const refreshSessions: ChatSessionData[] = refreshResponse.data;
              const refreshBlueprintSessions = refreshSessions.filter(
                (session) => session.blueprint_id === blueprintId && session.blueprint_exists
              );
              const refreshTransformedSessions = await transformApiDataToSessions(refreshBlueprintSessions);
              refreshTransformedSessions.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

              setSessions(refreshTransformedSessions);

              // Find the new session in the updated list and select it
              const newSession = refreshTransformedSessions.find((s) => s.id === newSessionId);
              if (newSession) {
                setSelectedSession(newSession);
              }
            })
            .catch((refreshError) => {
              // If refresh fails, that's okay - we already have the session selected
              console.error('Error refreshing sessions list:', refreshError);
            });
        } catch (createError: any) {
          console.error('Error auto-creating new chat:', createError);
          // Don't show toast for auto-creation errors, just log
        }
      } else if (transformedSessions.length > 0 && !selectedSession) {
        // Auto-select the first session if available and no session is selected
        const firstSession = transformedSessions[0];
        await handleSessionSelect(firstSession);
      }
    } catch (error: any) {
      console.error('Error fetching chat sessions:', error);
      toast({
        title: 'Error',
        description: 'Failed to load chat sessions',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, user, blueprintId, selectedSession, runId, transformApiDataToSessions, toast]);

  // Handle session selection
  const handleSessionSelect = useCallback(
    async (session: ChatSession) => {
      setSelectedSession(session);

      // If messages are already loaded for this session, use them
      if (session.messages && session.messages.length > 0) {
        // Pass raw backend messages to ChatInterface - it will handle the transformation
        setChatHistory(session.messages);
        setRunId(session.id);
      } else {
        // Otherwise, fetch the session state
        const stateData = await fetchSessionState(session.id);
        if (stateData && stateData.messages) {
          // Update the session with loaded messages
          const updatedSession = {
            ...session,
            messages: stateData.messages,
            preview: getPreviewText(stateData.messages),
          };
          setSelectedSession(updatedSession);

          // Update the session in the list
          setSessions((prevSessions) => prevSessions.map((s) => (s.id === session.id ? updatedSession : s)));

          // Pass raw backend messages to ChatInterface - it will handle the transformation
          setChatHistory(stateData.messages);
          setRunId(session.id);
        }
      }
    },
    [fetchSessionState]
  );

  // Handle delete chat
  const handleDeleteChat = useCallback((session: ChatSession, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent session selection when clicking delete
    setChatToDelete(session);
    setShowDeleteModal(true);
  }, []);

  const confirmDeleteChat = useCallback(async () => {
    if (!chatToDelete) return;

    setIsDeleting(true);
    try {
      await axios.delete(`/sessions/session.delete?sessionId=${chatToDelete.id}`);

      // Remove the deleted session from the list
      setSessions((prevSessions) => prevSessions.filter((session) => session.id !== chatToDelete.id));

      // If the deleted session was selected, clear the selection
      if (selectedSession?.id === chatToDelete.id) {
        setSelectedSession(null);
        setChatHistory([]);
        setRunId(null);
      }

      setShowDeleteModal(false);
      setChatToDelete(null);

      toast({
        title: 'Success',
        description: 'Chat session deleted successfully',
      });
    } catch (error: any) {
      console.error('Error deleting chat session:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to delete chat session',
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
    }
  }, [chatToDelete, selectedSession, toast]);

  const cancelDeleteChat = useCallback(() => {
    setShowDeleteModal(false);
    setChatToDelete(null);
  }, []);

  // Handle new chat creation
  const handleNewChat = useCallback(async () => {
    if (!blueprintId || !user) return;

    setIsCreatingSession(true);
    try {
      const response = await axios.post('/sessions/user.session.create', {
        blueprintId: blueprintId,
        userId: user.username,
        metadata: { source: 'public_link' },
      });

      const newSessionId = response.data;

      // Create a temporary session object for the new session
      const tempSession: ChatSession = {
        id: newSessionId,
        blueprintId: blueprintId,
        title: 'New Chat',
        lastActive: 'Just now',
        timestamp: new Date(),
        preview: 'New conversation',
        messages: [],
        blueprintExists: true,
        fromSharedLink: true,
      };

      // Select the new session immediately
      setSelectedSession(tempSession);
      setChatHistory([]);
      setRunId(newSessionId);

      // Refresh sessions list to get proper data (this will update the list but preserve selection)
      const response2 = await axios.get(`/sessions/session.user.chat.get?userId=${user.username}`);
      const allSessions: ChatSessionData[] = response2.data;
      const blueprintSessions = allSessions.filter(
        (session) => session.blueprint_id === blueprintId && session.blueprint_exists
      );
      const transformedSessions = await transformApiDataToSessions(blueprintSessions);
      transformedSessions.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

      // Update sessions list, but keep the selected session if it matches
      setSessions(transformedSessions);

      // Find the new session in the updated list and select it
      const newSession = transformedSessions.find((s) => s.id === newSessionId);
      if (newSession) {
        setSelectedSession(newSession);
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Failed to create new chat',
        variant: 'destructive',
      });
    } finally {
      setIsCreatingSession(false);
    }
  }, [blueprintId, user, transformApiDataToSessions, toast]);

  // Trigger execution
  const triggerExecution = useCallback(
    async (sessionPayload: any): Promise<string> => {
      if (!runId) {
        throw new Error('No session available');
      }

      // Check sharing status before allowing execution (fresh check each time)
      if (blueprintId) {
        try {
          const statusResponse = await getPublicUsageScope(blueprintId);
          const sharingDisabled = statusResponse.public_usage_scope !== true;
          if (sharingDisabled) {
            throw new Error("This workflow's chat sharing has been disabled and can no longer be continued.");
          }
        } catch (error: any) {
          // If status check fails or sharing is disabled, prevent execution
          if (error.message && error.message.includes('disabled')) {
            throw error; // Re-throw the disabled error
          }
          throw new Error("This workflow's chat sharing has been disabled and can no longer be continued.");
        }
      }

      try {
        // Use fetch for streaming response (axios doesn't handle streams well)
        const response = await fetch(`/api2/sessions/user.session.execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            sessionId: runId,
            inputs: sessionPayload.inputs || {},
            stream: true,
            streamMode: ['custom'],
            scope: 'public',
            loggedInUser: user?.username || '',
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Read the stream to completion (streaming updates are handled by ChatInterface via StreamingDataContext)
        if (response.body) {
          const reader = response.body.getReader();
          const decoder = new TextDecoder();

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              // Decode but don't process - ChatInterface handles streaming separately
              decoder.decode(value, { stream: true });
            }
          } finally {
            reader.releaseLock();
          }
        }

        // After stream completes, fetch the final output from session state
        const sessionResponse = await axios.get(`/sessions/session.state.get?sessionId=${runId}`);

        const output = sessionResponse.data.output;

        // Return the output if available, otherwise return a default message
        return output && output.trim() !== '' ? output : 'Execution completed, but no output was generated.';
      } catch (error: any) {
        console.error('Error in triggerExecution:', error);
        throw new Error(error.response?.data?.error || error.message || 'Failed to execute session');
      }
    },
    [runId, blueprintId, user]
  );

  // Load chat sessions when authenticated and blueprint is available
  useEffect(() => {
    if (isAuthenticated && user && blueprintId) {
      fetchChatSessions();
    }
  }, [isAuthenticated, user, blueprintId, fetchChatSessions]);

  return {
    sessions,
    selectedSession,
    isLoading,
    isCreatingSession,
    isDeleting,
    chatHistory,
    runId,
    handleNewChat,
    handleSessionSelect,
    handleDeleteChat,
    confirmDeleteChat,
    cancelDeleteChat,
    triggerExecution,
    showDeleteModal,
    chatToDelete,
  };
};

