import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Users, Clock, ArrowUpRight, SplitSquareVertical } from 'lucide-react';
import ChatInterface from './ChatInterface';
import ExecutionStream from './ExecutionStream';

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

export default function ExecutionTab() {
  const [selectedSession, setSelectedSession] = useState(chatSessions[0]);
  const [showExecutionStream, setShowExecutionStream] = useState(false);
  const [isActiveChatSession, setIsActiveChatSession] = useState(true);

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
          className={`flex items-center gap-2 ${isActiveChatSession ? 'bg-[#03DAC6] hover:bg-opacity-80' : 'bg-gray-700 text-gray-300 cursor-not-allowed'}`}
          onClick={() => setShowExecutionStream(!showExecutionStream)}
          disabled={!isActiveChatSession}
        >
          <SplitSquareVertical className="h-4 w-4" />
          {showExecutionStream ? 'Hide' : 'Open'} Execution Stream
        </Button>
      </div>

      <div className="grid grid-cols-12 gap-6" style={{ height: 'calc(100vh - 230px)' }}>
        {/* Chat sessions sidebar */}
        <div className="col-span-12 md:col-span-3 lg:col-span-2">
          <Card className="bg-background-card shadow-card border-gray-800 h-full flex flex-col">
            <CardHeader className="py-3 px-4 border-b border-gray-800">
              <div className="flex justify-between items-center">
                <CardTitle className="text-sm font-medium">Available Chats</CardTitle>
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
                        ? 'border-[#8A2BE2] bg-[#8A2BE2] bg-opacity-10'
                        : 'border-transparent hover:bg-background-surface'
                    }`}
                    onClick={() => setSelectedSession(session)}
                    whileHover={{ x: 2 }}
                    transition={{ duration: 0.1 }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <MessageSquare className="h-4 w-4 mr-2 text-gray-400" />
                        <span className="text-sm font-medium truncate max-w-[120px]">{session.title}</span>
                      </div>
                    </div>
                    <div className="mt-1 flex items-center text-xs text-gray-400">
                      <Clock className="h-3 w-3 mr-1" />
                      <span>{session.lastActive}</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-500 truncate">{session.preview}</p>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Chat interface and execution stream */}
        {showExecutionStream ? (
          <>
            <div className="col-span-12 md:col-span-5 lg:col-span-5 h-full">
              <ChatInterface />
            </div>
            <div className="col-span-12 md:col-span-4 lg:col-span-5 h-full">
              <ExecutionStream />
            </div>
          </>
        ) : (
          <div className="col-span-12 md:col-span-9 lg:col-span-10 h-full">
            <ChatInterface />
          </div>
        )}
      </div>
    </div>
  );
}