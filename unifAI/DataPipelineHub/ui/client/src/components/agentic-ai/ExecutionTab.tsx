import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Users, Clock, ArrowUpRight, SplitSquareVertical } from "lucide-react";
import ChatInterface from "./chat/ChatInterface";
import ExecutionStream from "./ExecutionStream";
import { GraphNode } from "../../pages/AgenticAI"
import axios, { AXIOS_AGENTS_IP } from '../../http/axiosAgentConfig'
import { useStreamingData } from './StreamingDataContext'

// Sample chat sessions
const chatSessions = [
  {
    id: '1',
    title: 'Customer Data Analysis',
    lastActive: '10 min ago',
    preview: 'Analysis of customer support ticket patterns...',
  },
  {
    id: '2',
    title: 'Product Recommendation',
    lastActive: '2 hours ago',
    preview: 'Personalized product suggestions based on user behavior...',
  },
  {
    id: '3',
    title: 'Sales Forecast',
    lastActive: '1 day ago',
    preview: 'Quarterly sales prediction based on historical data...',
  },
  {
    id: '4',
    title: 'Competitor Analysis',
    lastActive: '3 days ago',
    preview: 'In-depth analysis of top 3 competitors in the market...',
  },
  {
    id: '5',
    title: 'Email Campaign Draft',
    lastActive: '1 week ago',
    preview: 'Creating email templates for the upcoming marketing campaign...',
  },
];

export type SessionPayload = {
  sessionId: string;
  inputs: {"user_prompt": string},
  stream: boolean,
};

type ExecutionTabProps = {
  runId: string | null;
  selectedGraphNodes: GraphNode[] | null;
};

type ChunkData = {
  node: string;
  type: 'llm_token' | 'complete';
  chunk?: string;
  state?: {
    user_prompt?: string;
  };
};



export default function ExecutionTab({
  runId, selectedGraphNodes
}: ExecutionTabProps): React.ReactElement {
  const [selectedSession, setSelectedSession] = useState(chatSessions[0]);
  const [showExecutionStream, setShowExecutionStream] = useState(false);
  const [isActiveChatSession, setIsActiveChatSession] = useState(true);
  const [isLiveRequest, setIsLiveRequest] = useState(false);
  
  const { nodeListRef, forceUpdate } = useStreamingData();

  // Tracks each node's streaming state.
  // Aggregates chunks per node.
  // Marks a node as DONE when a type: "complete" event is received for it.
  // Cleanly handles streaming via ReadableStream.
  // This follows clean architecture, maintains readability, and ensures correctness even in noisy or unpredictable stream outputs.

  // Extracts multiple well-formed ["custom", {...}] chunks from the stream text.
  const parseStreamChunk = (chunk: string): any[] => {
    const parsedChunks: any[] = [];
    const pattern = /\["custom",\s*(\{.*?\})\]/g;
    let match: RegExpExecArray | null;

    while ((match = pattern.exec(chunk)) !== null) {
      try {
        const json = JSON.parse(match[1]);
        parsedChunks.push(json);
      } catch (e) {
        console.warn("Failed to parse stream JSON chunk:", match[1]);
      }
    }

    return parsedChunks;
  };

  // Maintains and updates a list of nodes and their stream state (PROGRESS or DONE) while aggregating text.
  const updateNodeList = (chunkData: ChunkData) => {
    const { node, type, chunk, state } = chunkData;
    const currentText = chunk ?? state?.user_prompt ?? '';
    const map = nodeListRef.current;
  
    const existing = map.get(node);
  
    if (!existing) {
      map.set(node, {
        node_name: node,
        stream: type === 'complete' ? 'DONE' : 'PROGRESS',
        text: currentText,
      });
    } else {
      if (type === 'llm_token' && chunk) {
        existing.text += chunk;
      } else if (type === 'complete') {
        existing.stream = 'DONE';
        if (state?.user_prompt && existing.text.trim() === '') {
          existing.text = state.user_prompt;
        }
      }
    }
    // forceUpdate(); // trigger a re-render if needed
  };

  // Reads the stream, decodes it, parses chunks, and updates state cleanly.
  const triggerExecution = async (sessionPayload: SessionPayload) => {
    try {
      setIsLiveRequest(true);
      const response = await fetch(`${AXIOS_AGENTS_IP}/api/sessions/user.session.execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sessionPayload),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      if (!response.body) throw new Error('ReadableStream not supported!');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parsedObjects = parseStreamChunk(buffer);

        if (parsedObjects.length === 0) continue;

        for (const chunkData of parsedObjects) {
          updateNodeList(chunkData);
          // console.log(
          //   JSON.stringify(Array.from(nodeListRef.current.entries()), null, 2)
          // );
        }

        // Clear buffer after parsing
        buffer = '';
      }

      console.log('Streaming completed.');
      console.log('Final Node List:', nodeListRef.current);
    } catch (error) {
      console.error('Error communicating with chat API', error);
    } finally {
          setIsLiveRequest(false);
          // TODO: Trigger API to get the state of the execution, finally return the final_answer
          return "---------------------------------------------------------------------------------------------------- FUTURE ANSWER -----------------------------------------------------------------------------------------"
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-heading font-semibold">AI Assistant</h2>
          <p className="text-sm text-gray-400 mt-1">
            Interact with your AI assistant and monitor execution details
          </p>
        </div>
        <Button
          className={`flex items-center gap-2 ${isActiveChatSession ? "bg-[#03DAC6] hover:bg-opacity-80" : "bg-gray-700 text-gray-300 cursor-not-allowed"}`}
          onClick={() => setShowExecutionStream(!showExecutionStream)}
          disabled={!isActiveChatSession}
        >
          <SplitSquareVertical className="h-4 w-4" />
          {showExecutionStream ? "Hide" : "Open"} Execution Stream
        </Button>
      </div>

      <div
        className="grid grid-cols-12 gap-6"
        style={{ height: "calc(100vh - 230px)" }}
      >
        {/* Chat sessions sidebar */}
        <div className="col-span-12 md:col-span-3 lg:col-span-2">
          <Card className="bg-background-card shadow-card border-gray-800 h-full flex flex-col">
            <CardHeader className="py-3 px-4 border-b border-gray-800">
              <div className="flex justify-between items-center">
                <CardTitle className="text-sm font-medium">
                  Available Chats
                </CardTitle>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                  <Users className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0 flex-grow overflow-y-auto">
              <div className="py-2">
                {chatSessions.map((session) => (
                  <motion.div
                    key={session.id}
                    className={`px-4 py-3 border-l-2 cursor-pointer ${
                      selectedSession.id === session.id
                        ? "border-[#8A2BE2] bg-[#8A2BE2] bg-opacity-10"
                        : "border-transparent hover:bg-background-surface"
                    }`}
                    onClick={() => setSelectedSession(session)}
                    whileHover={{ x: 2 }}
                    transition={{ duration: 0.1 }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <MessageSquare className="h-4 w-4 mr-2 text-gray-400" />
                        <span className="text-sm font-medium truncate max-w-[120px]">
                          {session.title}
                        </span>
                      </div>
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
            </CardContent>
          </Card>
        </div>
        
        {/* ChatInterface with conditional className */}
        <div className={`col-span-12 ${showExecutionStream ? 'md:col-span-5 lg:col-span-5' : 'md:col-span-9 lg:col-span-10'} h-full`}>
          <ChatInterface 
            runId={runId || selectedSession.id} 
            triggerExecution={triggerExecution} 
          />
        </div>

        {/* ExecutionStream only renders when showExecutionStream is true */}
        {showExecutionStream && (
          <div className="col-span-12 md:col-span-4 lg:col-span-5 h-full">
            <ExecutionStream 
              runId={runId || selectedSession.id} 
              selectedGraphNodes={selectedGraphNodes} 
              isLiveRequest={isLiveRequest} 
            />
          </div>
        )}
      </div>
    </div>
  );
}