import React, { useState, useEffect } from "react";
import { useRoute } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import axios from "@/http/axiosAgentConfig";
import ChatInterface from "@/components/agentic-ai/chat/ChatInterface";
import { SessionPayload } from "@/components/agentic-ai/ExecutionTab";
import { StreamingDataProvider } from "@/components/agentic-ai/StreamingDataContext";
import { Loader2, MessageSquare, Clock, Plus, Trash2 } from "lucide-react";
import { FaSignOutAlt } from "react-icons/fa";
import { motion } from "framer-motion";
import SimpleTooltip from "@/components/shared/SimpleTooltip";
import { useTheme } from "@/contexts/ThemeContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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

// Backend message format
interface BackendChatMessage {
  content: string;
  role: "user" | "assistant";
}

interface ChatSessionData {
  metadata: Record<string, any>;
  blueprint_id: string;
  session_id: string;
  started_at: string;
  blueprint_exists: boolean;
}

interface SessionStateData {
  final_output: string;
  messages: BackendChatMessage[];
}

interface ChatSession {
  id: string;
  blueprintId: string;
  title: string;
  lastActive: string;
  timestamp: Date;
  preview: string;
  messages: BackendChatMessage[];
  blueprintExists: boolean;
  fromSharedLink?: boolean;
}

export default function ChatOnlyPage() {
  const [, params] = useRoute("/chat/:token");
  const token = params?.token;
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const { toast } = useToast();
  const { primaryHex } = useTheme();
  
  const [blueprintId, setBlueprintId] = useState<string | null>(null);
  const [blueprintName, setBlueprintName] = useState<string>("");
  const [blueprintOwner, setBlueprintOwner] = useState<string>("");
  const [runId, setRunId] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [chatHistory, setChatHistory] = useState<BackendChatMessage[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<ChatSession | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Validate token and get blueprint info
  useEffect(() => {
    if (!token) {
      setIsValidating(false);
      return;
    }

    const validateToken = async () => {
      try {
        const response = await axios.get(
          `/shares/public-chat.validate?blueprintId=${token}`
        );
        
        if (response.data.valid) {
          setBlueprintId(token);
          setBlueprintName(response.data.blueprint_name || "Unnamed Workflow");
          
          // Always fetch blueprint info to get owner from blueprints collection
          try {
            const blueprintInfoResponse = await axios.get(`/blueprints/blueprint.info.get?blueprintId=${token}`);
            if (blueprintInfoResponse.data) {
              // Update blueprint name from blueprint info (most accurate)
              if (blueprintInfoResponse.data.blueprint_name) {
                setBlueprintName(blueprintInfoResponse.data.blueprint_name);
              }
              // Get owner from blueprint document
              if (blueprintInfoResponse.data.owner_user_id) {
                setBlueprintOwner(blueprintInfoResponse.data.owner_user_id);
              }
            }
          } catch (error) {
            console.error('Error fetching blueprint info:', error);
            // Fallback to validation response owner if available
            if (response.data.owner_user_id) {
              setBlueprintOwner(response.data.owner_user_id);
            }
          }
        } else {
          const errorMsg = response.data.error || "This chat link is no longer valid or has been disabled";
          setValidationError(errorMsg);
        }
      } catch (error: any) {
        const errorMsg = error.response?.data?.error || "Failed to validate chat link";
        setValidationError(errorMsg);
      } finally {
        setIsValidating(false);
      }
    };

    validateToken();
  }, [token, toast]);

  // Helper function to format timestamp
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Helper function to generate random title
  const generateRandomTitle = (index: number): string => {
    const titles = ["Chat Session", "Conversation", "Discussion", "Chat"];
    return `${titles[index % titles.length]} ${index + 1}`;
  };

  // Helper function to get preview text from messages
  const getPreviewText = (messages: BackendChatMessage[]): string => {
    if (!messages || messages.length === 0) return "No messages yet";
    const lastMessage = messages[messages.length - 1];
    return lastMessage.content.substring(0, 50) + (lastMessage.content.length > 50 ? "..." : "");
  };

  // Transform API data to ChatSession format
  const transformApiDataToSessions = (apiData: ChatSessionData[]): ChatSession[] => {
    return apiData.map((sessionData, index) => {
      const title = sessionData.metadata?.title || generateRandomTitle(index);
      const id = sessionData.session_id;
      const blueprintId = sessionData.blueprint_id;
      const blueprintExists = sessionData.blueprint_exists;
      const fromSharedLink = sessionData.metadata?.from_shared_link || false;
      const timestamp = new Date(sessionData.started_at);
      const lastActive = formatTimestamp(sessionData.started_at);
      const preview = "Click to load messages...";
      
      return {
        id,
        blueprintId,
        title: fromSharedLink ? `${title} (Shared Link)` : title,
        lastActive,
        timestamp,
        preview,
        messages: [],
        blueprintExists,
        fromSharedLink,
      };
    });
  };

  // Fetch session state (messages) for a specific session
  const fetchSessionState = async (sessionId: string): Promise<SessionStateData | null> => {
    try {
      const response = await axios.get(`/sessions/session.state.get?sessionId=${sessionId}`);
      return response.data;
    } catch (err) {
      console.error('Error fetching session state:', err);
      return null;
    }
  };

  // Load chat sessions for this user and blueprint
  const fetchChatSessions = async () => {
    if (!isAuthenticated || !user || !blueprintId) {
      return;
    }

    setIsLoadingSessions(true);
    try {
      const response = await axios.get(`/sessions/session.user.chat.get?userId=${user.username}`);
      const sessions: ChatSessionData[] = response.data;
      
      // Filter sessions for this blueprint
      const blueprintSessions = sessions.filter(
        (session) => session.blueprint_id === blueprintId && session.blueprint_exists
      );
      
      // Transform to ChatSession format
      const transformedSessions = transformApiDataToSessions(blueprintSessions);
      
      // Sort by timestamp (most recent first)
      transformedSessions.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
      
      setChatSessions(transformedSessions);
      
      // Auto-select the first session if available and no session is selected
      if (transformedSessions.length > 0 && !selectedSession) {
        const firstSession = transformedSessions[0];
        await handleSessionSelect(firstSession);
      }
    } catch (error: any) {
      console.error('Error fetching chat sessions:', error);
      toast({
        title: "Error",
        description: "Failed to load chat sessions",
        variant: "destructive",
      });
    } finally {
      setIsLoadingSessions(false);
    }
  };

  // Handle session selection
  const handleSessionSelect = async (session: ChatSession) => {
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
        setChatSessions(prevSessions =>
          prevSessions.map(s => s.id === session.id ? updatedSession : s)
        );
        
        // Pass raw backend messages to ChatInterface - it will handle the transformation
        setChatHistory(stateData.messages);
        setRunId(session.id);
      }
    }
  };

  // Handle delete chat
  const handleDeleteChat = (session: ChatSession, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent session selection when clicking delete
    setChatToDelete(session);
    setShowDeleteModal(true);
  };

  const confirmDeleteChat = async () => {
    if (!chatToDelete) return;

    setIsDeleting(true);
    try {
      await axios.delete(`/sessions/session.delete?sessionId=${chatToDelete.id}`);

      // Remove the deleted session from the list
      setChatSessions(prevSessions => prevSessions.filter(session => session.id !== chatToDelete.id));

      // If the deleted session was selected, clear the selection
      if (selectedSession?.id === chatToDelete.id) {
        setSelectedSession(null);
        setChatHistory([]);
        setRunId(null);
      }

      setShowDeleteModal(false);
      setChatToDelete(null);
      
      toast({
        title: "Success",
        description: "Chat session deleted successfully",
      });
    } catch (error: any) {
      console.error('Error deleting chat session:', error);
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to delete chat session",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDeleteChat = () => {
    setShowDeleteModal(false);
    setChatToDelete(null);
  };

  // Handle new chat creation
  const handleNewChat = async () => {
    if (!blueprintId || !user) return;
    
    setIsCreatingSession(true);
    try {
      const response = await axios.post("/sessions/user.session.create", {
        blueprintId: blueprintId,
        userId: user.username,
        metadata: {},
        fromSharedLink: true,
      });
      
      const newSessionId = response.data;
      
      // Create a temporary session object for the new session
      const tempSession: ChatSession = {
        id: newSessionId,
        blueprintId: blueprintId,
        title: "New Chat",
        lastActive: "Just now",
        timestamp: new Date(),
        preview: "New conversation",
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
      const sessions: ChatSessionData[] = response2.data;
      const blueprintSessions = sessions.filter(
        (session) => session.blueprint_id === blueprintId && session.blueprint_exists
      );
      const transformedSessions = transformApiDataToSessions(blueprintSessions);
      transformedSessions.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
      
      // Update sessions list, but keep the selected session if it matches
      setChatSessions(transformedSessions);
      
      // Find the new session in the updated list and select it
      const newSession = transformedSessions.find(s => s.id === newSessionId);
      if (newSession) {
        setSelectedSession(newSession);
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to create new chat",
        variant: "destructive",
      });
    } finally {
      setIsCreatingSession(false);
    }
  };

  // Load chat sessions when authenticated and blueprint is available
  useEffect(() => {
    if (isAuthenticated && user && blueprintId) {
      fetchChatSessions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user, blueprintId]);


  const triggerExecution = async (sessionPayload: SessionPayload): Promise<string> => {
    if (!runId) {
      throw new Error("No session available");
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
          streamMode: ["custom"],
          scope: "public",
          loggedInUser: user?.username || "",
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
      const sessionResponse = await axios.get(
        `/sessions/session.state.get?sessionId=${runId}`
      );
      
      const output = sessionResponse.data.output;
      
      // Return the output if available, otherwise return a default message
      return output && output.trim() !== "" 
        ? output 
        : "Execution completed, but no output was generated.";
    } catch (error: any) {
      console.error("Error in triggerExecution:", error);
      throw new Error(error.response?.data?.error || error.message || "Failed to execute session");
    }
  };

  // Show loading state
  if (authLoading || isValidating) {
    return (
      <div className="flex items-center justify-center h-screen bg-background-dark">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Show authentication required
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen bg-background-dark">
        <div className="text-center">
          <p className="text-white mb-4">Authentication required to access this chat</p>
          <p className="text-gray-400 text-sm">Please log in to continue</p>
        </div>
      </div>
    );
  }

  // Show invalid link
  if (!blueprintId || validationError) {
    return (
      <div className="flex items-center justify-center h-screen bg-background-dark">
        <div className="text-center">
          <p className="text-white mb-2">Invalid Chat Link</p>
          <p className="text-gray-400 text-sm">
            {validationError || "This chat link is no longer valid or has been disabled"}
          </p>
        </div>
      </div>
    );
  }


  return (
    <div className="flex flex-col h-screen bg-background-dark">
      {/* Header with Unifai branding and user info */}
      <div className="bg-background-card border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-md bg-gradient-to-r from-primary to-gray-500 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 12H7M17 12H21M12 3V7M12 17V21M5 19L8 16M16 8L19 5M19 19L16 16M5 5L8 8" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h1 className="text-xl font-bold text-white">UnifAI</h1>
          </div>
          <div className="h-6 w-px bg-gray-700" />
          <div className="flex items-center">
            <p className="text-sm text-gray-400">{blueprintName}</p>
            {blueprintOwner && (
              <span className="text-xs text-gray-500 ml-2">(workflow shared by {blueprintOwner})</span>
            )}
          </div>
        </div>
        
        {/* User Profile with Logout - matching regular UnifAI header */}
        <div className="px-4 py-3 border-l border-gray-800">
          <div className="flex items-center space-x-3">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ background: `linear-gradient(90deg, #6B7280, ${primaryHex || '#8A2BE2'})` }}
            >
              <span className="text-sm font-medium text-white">
                {user?.name
                  ?.split(' ')
                  .filter(Boolean)
                  .map(part => part[0].toUpperCase())
                  .join('') || user?.username?.[0].toUpperCase() || 'U'}
              </span>
            </div>
            
            <motion.div
              initial={false}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2 }}
              className="flex-grow"
            >
              <h4 className="text-sm font-medium text-white">{user?.name || user?.username || "User"}</h4>
            </motion.div>
            
            <motion.div
              initial={false}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2 }}
            >
              <SimpleTooltip content={<p>Sign out</p>}>
                <button 
                  onClick={logout}
                  className="mt-2 text-gray-400 hover:text-white transition-colors"
                >
                  <FaSignOutAlt />
                </button>
              </SimpleTooltip>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Main Content Area with Sidebar */}
      <div className="flex-1 overflow-hidden flex">
        {/* Chat History Sidebar */}
        <div className="w-80 border-r border-gray-800 bg-background-card flex flex-col flex-shrink-0">
          <Card className="bg-background-card shadow-card border-0 h-full flex flex-col">
            <CardHeader className="py-3 px-4 border-b border-gray-800">
              <div className="flex justify-between items-center">
                <CardTitle className="text-sm font-medium">
                  Chat History ({chatSessions.length})
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-primary hover:bg-primary/20"
                  onClick={handleNewChat}
                  disabled={isCreatingSession}
                  title="Start new chat"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0 flex-grow overflow-y-auto">
              {isLoadingSessions ? (
                <div className="p-4 text-center">
                  <Loader2 className="h-5 w-5 animate-spin mx-auto text-primary" />
                </div>
              ) : chatSessions.length === 0 ? (
                <div className="p-4 text-center text-gray-400 text-sm">
                  No chat sessions yet. Click + to start a new chat.
                </div>
              ) : (
                <div className="py-2">
                  {chatSessions.map((session) => (
                    <motion.div
                      key={session.id}
                      className={`group px-4 py-3 border-l-2 cursor-pointer ${
                        selectedSession?.id === session.id
                          ? "border-[hsl(var(--primary))] bg-primary/20"
                          : "border-transparent hover:bg-background-surface"
                      } ${
                        !session.blueprintExists
                          ? "opacity-50 bg-gray-800/30"
                          : ""
                      }`}
                      onClick={() => handleSessionSelect(session)}
                      whileHover={{ x: 2 }}
                      transition={{ duration: 0.1 }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center min-w-0 flex-1">
                          <MessageSquare className="h-4 w-4 mr-2 text-gray-400 flex-shrink-0" />
                          <span className="text-sm font-medium truncate text-white">
                            {session.title}
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-gray-400 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                          onClick={(e) => handleDeleteChat(session, e)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                      <div className="mt-1 flex items-center text-xs text-gray-400">
                        <Clock className="h-3 w-3 mr-1" />
                        <span>{session.lastActive}</span>
                      </div>
                      <p className="mt-1 text-xs text-gray-500 truncate">
                        {session.preview}
                      </p>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden">
          {!runId ? (
            <div className="flex items-center justify-center h-full bg-background-dark">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-400">Select a chat session or start a new one</p>
              </div>
            </div>
          ) : (
            <StreamingDataProvider>
              <ChatInterface
                runId={runId}
                triggerExecution={triggerExecution}
                initialMessages={chatHistory}
                blueprintExists={true}
                isBlueprintGraphHidden={true}
                isChatOnlyMode={true}
              />
            </StreamingDataProvider>
          )}
        </div>
      </div>

      {/* Delete Chat Confirmation Modal */}
      <AlertDialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
        <AlertDialogContent className="bg-background-card border-gray-800">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Chat</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{chatToDelete?.title}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel 
              onClick={cancelDeleteChat}
              className="bg-background-dark border-gray-700 hover:bg-background-surface"
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteChat}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}