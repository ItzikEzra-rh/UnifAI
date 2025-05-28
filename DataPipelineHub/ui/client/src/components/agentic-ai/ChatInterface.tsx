import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Trash2, Settings, ChevronDown, ChevronRight, AlertCircle } from "lucide-react";
import axios from '../../http/axiosAgentConfig'
import { SessionPayload } from './ExecutionTab'
import { useStreamingData, NodeEntry } from "./StreamingDataContext"

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  streamLogs?: StreamLogEntry[];
  finalAnswer?: string;
}

interface StreamLogEntry {
  nodeId: string;
  nodeName: string;
  message: string;
  status: 'processing' | 'complete' | 'error';
  isExpanded?: boolean;
}

interface ChatInterfaceProps {
  runId?: string;
  triggerExecution: (sessionPayload: SessionPayload) => Promise<string>
}

export default function ChatInterface({ runId, triggerExecution }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your AI assistant. How can I help you process your data today?',
      sender: 'ai',
      timestamp: new Date(),
    },
  ]);
  
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentStreamingMessageId, setCurrentStreamingMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const { nodeListRef } = useStreamingData();

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Map stream type to status
  const mapStreamToStatus = (stream: string): 'processing' | 'complete' | 'error' => {
    switch (stream) {
      case 'PROGRESS':
        return 'processing';
      case 'ERROR':
        return 'error';
      case 'COMPLETE':
        return 'complete';
      default:
        return 'processing';
    }
  };

  // Start streaming logs for the current message
  const startStreamingLogs = (messageId: string) => {
    if (streamingIntervalRef.current) {
      clearInterval(streamingIntervalRef.current);
    }

    streamingIntervalRef.current = setInterval(() => {
      const list = Array.from(nodeListRef.current.values());
      
      if (list.length > 0) {
        setMessages(prevMessages => 
          prevMessages.map(msg => {
            if (msg.id === messageId && msg.sender === 'ai') {
              const updatedStreamLogs: StreamLogEntry[] = [];
              
              // Process each entry from nodeListRef
              list.forEach(entry => {
                const existingLog = msg.streamLogs?.find(log => log.nodeId === entry.node_name);
                
                updatedStreamLogs.push({
                  nodeId: entry.node_name,
                  nodeName: entry.node_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                  message: entry.text,
                  status: mapStreamToStatus(entry.stream),
                  isExpanded: existingLog?.isExpanded || false,
                });
              });
              
              return {
                ...msg,
                streamLogs: updatedStreamLogs,
              };
            }
            return msg;
          })
        );
      }
    }, 500);
  };

  // Stop streaming logs and mark all as complete
  const stopStreamingLogs = (messageId?: string) => {
    if (streamingIntervalRef.current) {
      clearInterval(streamingIntervalRef.current);
      streamingIntervalRef.current = null;
      
      // Mark all processing nodes as complete when streaming stops
      const targetMessageId = messageId || currentStreamingMessageId;
      if (targetMessageId) {
        setMessages(prevMessages => 
          prevMessages.map(msg => {
            if (msg.id === targetMessageId && msg.sender === 'ai') {
              return {
                ...msg,
                streamLogs: msg.streamLogs?.map(log => ({
                  ...log,
                  status: log.status === 'processing' ? 'complete' : log.status
                }))
              };
            }
            return msg;
          })
        );
      }
    }
  };

  // Toggle expansion of a specific node log
  const toggleNodeExpansion = (messageId: string, nodeId: string) => {
    setMessages(prevMessages =>
      prevMessages.map(msg => {
        if (msg.id === messageId) {
          return {
            ...msg,
            streamLogs: msg.streamLogs?.map(log =>
              log.nodeId === nodeId
                ? { ...log, isExpanded: !log.isExpanded }
                : log
            ),
          };
        }
        return msg;
      })
    );
  };

  const getSessionState = async (sid: string) => {
    try {
      // Make API call to get the session state
      const response = await axios.get(`/api/session.state.get?sessionId=${sid}`);
      const data = response.data
      
      if (data && data.response) {
        return data.response;
      }

      return "I'm sorry, I couldn't retrieve a response for your query.";
    } catch (error) {
      console.error("Failed to get session state:", error);
      return "I'm sorry, I couldn't retrieve a response for your query.";
    }
  };

  // User sends message → Creates an AI message with empty streamLogs
  // Streaming starts → Interval polls for node updates and updates the message
  // Live updates → Each node appears/updates as data becomes available
  // User interaction → Can expand/collapse individual node logs
  // Completion → Final answer appears and streaming stops
  // Cleanup → All intervals are properly cleared
  const handleSendMessage = async () => {
    if (inputMessage.trim() === '') return;
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);
    
    // Create initial AI message for streaming
    const streamingMessageId = (Date.now() + 1).toString();
    const initialAiMessage: Message = {
      id: streamingMessageId,
      content: '',
      sender: 'ai',
      timestamp: new Date(),
      streamLogs: [],
    };
    
    setMessages(prev => [...prev, initialAiMessage]);
    setCurrentStreamingMessageId(streamingMessageId);
    
    // Start streaming logs
    startStreamingLogs(streamingMessageId);
    
    try {
      const sessionPayload: SessionPayload = {
        "sessionId": runId || "",
        "inputs": {"user_prompt": inputMessage},
        "stream": true,
      };

      const response = await triggerExecution(sessionPayload);

      // Update the message with final answer
      setMessages(prev =>
        prev.map(msg => {
          if (msg.id === streamingMessageId) {
            return {
              ...msg,
              finalAnswer: response,
            };
          }
          return msg;
        })
      );
    } catch (error) {
      console.error("Error in chat interaction:", error);
      
      // Update with error message
      setMessages(prev =>
        prev.map(msg => {
          if (msg.id === streamingMessageId) {
            return {
              ...msg,
              finalAnswer: "I'm sorry, there was an error processing your request.",
            };
          }
          return msg;
        })
      );
    } finally {
      setIsTyping(false);
      stopStreamingLogs(streamingMessageId);
      setCurrentStreamingMessageId(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        content: 'Chat cleared. How can I help you with your data pipeline?',
        sender: 'ai',
        timestamp: new Date(),
      },
    ]);
    stopStreamingLogs();
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      stopStreamingLogs();
    };
  }, []);

  // Status indicator component
  const StatusIndicator = ({ status }: { status: string }) => {
    switch (status) {
      case 'processing':
        return (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
            className="inline-block"
          >
            <AlertCircle className="h-3 w-3 text-[#FFB300]" />
          </motion.div>
        );
      case 'complete':
        return <div className="w-3 h-3 bg-[#00E676] rounded-full" />;
      case 'error':
        return <div className="w-3 h-3 bg-[#FF1744] rounded-full" />;
      default:
        return <div className="w-3 h-3 bg-gray-400 rounded-full" />;
    }
  };

  // Stream log component
  const StreamLogDisplay = ({ message }: { message: Message }) => {
    if (!message.streamLogs || message.streamLogs.length === 0) {
      return null;
    }

    return (
      <div className="mt-3 space-y-2 w-full">
        {message.streamLogs.map((log) => (
          <div key={log.nodeId} className="border border-gray-700 rounded-lg overflow-hidden w-full">
            <div
              className="flex items-center justify-between p-3 bg-gray-800 cursor-pointer hover:bg-gray-750 transition-colors w-full"
              onClick={() => toggleNodeExpansion(message.id, log.nodeId)}
            >
              <div className="flex items-center space-x-2">
                <StatusIndicator status={log.status} />
                <span className="text-sm font-medium text-gray-200">
                  {log.nodeName}
                </span>
                <span className="text-xs text-gray-400">
                  {log.status === 'processing' ? 'Generating...' : 
                   log.status === 'complete' ? 'Complete' : 'Error'}
                </span>
              </div>
              {log.isExpanded ? (
                <ChevronDown className="h-4 w-4 text-gray-400" />
              ) : (
                <ChevronRight className="h-4 w-4 text-gray-400" />
              )}
            </div>
            <AnimatePresence>
              {log.isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden w-full"
                >
                  <div className="p-3 bg-gray-900 border-t border-gray-700 w-full">
                    <div className={`text-sm font-mono whitespace-pre-wrap break-words w-full ${
                      log.status === 'error' ? 'text-[#FF1744]' : 'text-gray-300'
                    }`}>
                      {log.message || 'Processing...'}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    );
  };

  return (
    <Card className="bg-background-card shadow-card border-gray-800 flex flex-col h-full">
      <CardHeader className="py-4 px-6 flex flex-row justify-between items-center">
        <CardTitle className="text-lg font-heading">AI Assistant</CardTitle>
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={clearChat}
            className="text-gray-400 hover:text-gray-100"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-400 hover:text-gray-100"
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-grow overflow-hidden p-0 flex flex-col">
        <div className="flex-grow overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[90%] rounded-2xl p-3 ${
                    message.sender === 'user'
                      ? 'bg-[#8A2BE2] text-white rounded-tr-none'
                      : 'bg-background-dark border border-gray-800 rounded-tl-none'
                  }`}
                >
                  {message.sender === 'ai' && (message.streamLogs || message.finalAnswer) ? (
                    <div className="space-y-3 w-full">
                      {/* Stream logs display */}
                      <StreamLogDisplay message={message} />
                      
                      {/* Final answer */}
                      {message.finalAnswer && (
                        <div className="mt-4 pt-3 border-t border-gray-700 w-full">
                          <div className="flex items-center space-x-2 mb-2">
                            <div className="w-3 h-3 bg-[#00E676] rounded-full" />
                            <span className="text-sm font-medium text-gray-200">Final Answer</span>
                          </div>
                          <div className="text-sm text-gray-300">
                            {message.finalAnswer}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-sm">{message.content}</div>
                  )}
                  
                  <div className={`text-xs mt-2 ${message.sender === 'user' ? 'text-purple-200' : 'text-gray-400'}`}>
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              </motion.div>
            ))}
            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="flex justify-start"
              >
                <div className="bg-background-dark border border-gray-800 rounded-2xl rounded-tl-none p-3 max-w-[80%]">
                  <div className="flex space-x-1">
                    <motion.div
                      className="w-2 h-2 bg-gray-400 rounded-full"
                      animate={{ y: [0, -5, 0] }}
                      transition={{ repeat: Infinity, duration: 0.5, ease: "easeInOut" }}
                    />
                    <motion.div
                      className="w-2 h-2 bg-gray-400 rounded-full"
                      animate={{ y: [0, -5, 0] }}
                      transition={{ repeat: Infinity, duration: 0.5, ease: "easeInOut", delay: 0.1 }}
                    />
                    <motion.div
                      className="w-2 h-2 bg-gray-400 rounded-full"
                      animate={{ y: [0, -5, 0] }}
                      transition={{ repeat: Infinity, duration: 0.5, ease: "easeInOut", delay: 0.2 }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
        <div className="p-4 border-t border-gray-800">
          <div className="flex space-x-2">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your data..."
              className="bg-background-dark"
            />
            <Button
              onClick={handleSendMessage}
              disabled={inputMessage.trim() === '' || isTyping}
              className="bg-[#8A2BE2] hover:bg-[#7525c9]"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}