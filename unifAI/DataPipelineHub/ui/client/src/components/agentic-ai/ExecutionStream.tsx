import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Pause, Play, Trash2, Download, Info, AlertCircle, CheckCircle,
  Search, User, FileSearch, GitPullRequest, Database, Code, MessageSquare, Brain, Wrench, Layers
} from "lucide-react";

interface LogEntry {
  id: string;
  timestamp: Date;
  agent: string;
  message: string;
  status: 'info' | 'processing' | 'success' | 'error';
}

// Sample agent nodes for log filtering
const agentNodes = [
  {
    id: 'all',
    name: 'All Agents',
    description: 'Combined logs from all agents',
    icon: <Layers className="h-4 w-4 mr-2" />,
  },
  {
    id: 'user-query',
    name: 'User Query',
    description: 'User input processing',
    icon: <User className="h-4 w-4 mr-2" />,
  },
  {
    id: 'query-parser',
    name: 'Query Parser',
    description: 'Intent & entity extraction',
    icon: <Search className="h-4 w-4 mr-2" />,
  },
  {
    id: 'context-retriever',
    name: 'Context Retriever',
    description: 'Knowledge retrieval',
    icon: <FileSearch className="h-4 w-4 mr-2" />,
  },
  {
    id: 'planning-agent',
    name: 'Planning Agent',
    description: 'Task decomposition',
    icon: <GitPullRequest className="h-4 w-4 mr-2" />,
  },
  {
    id: 'research-agent',
    name: 'Research Agent',
    description: 'Information gathering',
    icon: <Database className="h-4 w-4 mr-2" />,
  },
  {
    id: 'tool-agent',
    name: 'Tool Agent',
    description: 'External tool usage',
    icon: <Wrench className="h-4 w-4 mr-2" />,
  },
  {
    id: 'response-generator',
    name: 'Response Generator',
    description: 'Output creation',
    icon: <MessageSquare className="h-4 w-4 mr-2" />,
  },
  {
    id: 'llm-response',
    name: 'LLM Response',
    description: 'Final answer generation',
    icon: <Brain className="h-4 w-4 mr-2" />,
  },
];

export default function ExecutionStream() {
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: '1',
      timestamp: new Date(),
      agent: 'System',
      message: 'Agentic AI system initialized and ready.',
      status: 'info',
    }
  ]);
  
  const [selectedNode, setSelectedNode] = useState(agentNodes[0]);
  const [autoscroll, setAutoscroll] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  
  // Filter logs based on selected node
  const filteredLogs = selectedNode.id === 'all' 
    ? logs 
    : logs.filter(log => log.agent === selectedNode.name);
  
  // Demo logs for simulation
  const demoLogs: LogEntry[] = [
    {
      id: '2',
      timestamp: new Date(),
      agent: 'User Input',
      message: 'Received query: "Analyze our customer support tickets and identify common issues."',
      status: 'info',
    },
    {
      id: '3',
      timestamp: new Date(),
      agent: 'Query Parser',
      message: 'Parsing user query. Identified intent: DATA_ANALYSIS with focus on CUSTOMER_SUPPORT_TICKETS.',
      status: 'processing',
    },
    {
      id: '4',
      timestamp: new Date(),
      agent: 'Query Parser',
      message: 'Query parsed successfully. Extracted entities: [customer_support, tickets, common_issues]',
      status: 'success',
    },
    {
      id: '5',
      timestamp: new Date(),
      agent: 'Context Retriever',
      message: 'Retrieving context from customer support database.',
      status: 'processing',
    },
    {
      id: '6',
      timestamp: new Date(),
      agent: 'Context Retriever',
      message: 'Successfully retrieved 1,245 support tickets from the last 30 days.',
      status: 'success',
    },
    {
      id: '7',
      timestamp: new Date(),
      agent: 'Planning Agent',
      message: 'Developing analysis plan. Steps: 1) Categorize tickets, 2) Identify frequency patterns, 3) Extract common themes.',
      status: 'processing',
    },
    {
      id: '8',
      timestamp: new Date(),
      agent: 'Planning Agent',
      message: 'Analysis plan created successfully.',
      status: 'success',
    },
    {
      id: '9',
      timestamp: new Date(),
      agent: 'Research Agent',
      message: 'Researching similar patterns from historical data.',
      status: 'processing',
    },
    {
      id: '10',
      timestamp: new Date(),
      agent: 'Research Agent',
      message: 'Research complete. Found 3 relevant historical patterns.',
      status: 'success',
    },
    {
      id: '11',
      timestamp: new Date(),
      agent: 'Tool Agent',
      message: 'Initializing text clustering algorithm for ticket categorization.',
      status: 'processing',
    },
    {
      id: '12',
      timestamp: new Date(),
      agent: 'Tool Agent',
      message: 'Error accessing NLP service: Rate limit exceeded.',
      status: 'error',
    },
    {
      id: '13',
      timestamp: new Date(),
      agent: 'Tool Agent',
      message: 'Retrying with backup NLP service.',
      status: 'processing',
    },
    {
      id: '14',
      timestamp: new Date(),
      agent: 'Tool Agent',
      message: 'Successfully categorized tickets into 7 distinct issue groups.',
      status: 'success',
    },
    {
      id: '15',
      timestamp: new Date(),
      agent: 'Response Generator',
      message: 'Generating comprehensive response based on analysis results.',
      status: 'processing',
    },
    {
      id: '16',
      timestamp: new Date(),
      agent: 'Response Generator',
      message: 'Response generated successfully.',
      status: 'success',
    },
    {
      id: '17',
      timestamp: new Date(),
      agent: 'System',
      message: 'Analysis complete. Results delivered to user interface.',
      status: 'info',
    },
  ];

  // Scroll to bottom when new logs are added
  useEffect(() => {
    if (autoscroll) {
      scrollToBottom();
    }
  }, [logs, autoscroll]);

  // Auto-scroll function
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Demo execution to simulate log entries
  useEffect(() => {
    let logIndex = 0;
    let intervalId: NodeJS.Timeout;

    if (isRunning && logIndex < demoLogs.length) {
      intervalId = setInterval(() => {
        if (logIndex < demoLogs.length) {
          const newLog = {
            ...demoLogs[logIndex],
            id: (Date.now() + logIndex).toString(),
            timestamp: new Date(),
          };
          
          setLogs(prevLogs => [...prevLogs, newLog]);
          logIndex++;
        } else {
          clearInterval(intervalId);
          setIsRunning(false);
        }
      }, 1500);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isRunning]);

  // Format timestamp
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Clear logs
  const clearLogs = () => {
    setLogs([
      {
        id: Date.now().toString(),
        timestamp: new Date(),
        agent: 'System',
        message: 'Execution logs cleared.',
        status: 'info',
      },
    ]);
  };

  // Toggle simulation
  const toggleSimulation = () => {
    setIsRunning(!isRunning);
  };

  // Status icon component
  const StatusIcon = ({ status }: { status: string }) => {
    switch (status) {
      case 'info':
        return <Info className="h-4 w-4 text-[#00B0FF]" />;
      case 'processing':
        return (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
          >
            <AlertCircle className="h-4 w-4 text-[#FFB300]" />
          </motion.div>
        );
      case 'success':
        return <CheckCircle className="h-4 w-4 text-[#00E676]" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-[#FF1744]" />;
      default:
        return <Info className="h-4 w-4 text-[#00B0FF]" />;
    }
  };

  return (
    <Card className="bg-background-card shadow-card border-gray-800 flex flex-col h-full">
      <CardHeader className="py-4 px-6 flex flex-row justify-between items-center">
        <CardTitle className="text-lg font-heading">Execution Stream</CardTitle>
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSimulation}
            className="text-gray-400 hover:text-gray-100"
          >
            {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearLogs}
            className="text-gray-400 hover:text-gray-100"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-400 hover:text-gray-100"
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-grow overflow-hidden p-0 flex flex-col">
        <div className="flex h-full">
          {/* Agent nodes sidebar */}
          <div className="w-1/5 border-r border-gray-800 bg-background-dark overflow-y-auto">
            <div className="py-3 px-4 border-b border-gray-800 bg-background-surface">
              <h3 className="text-sm font-medium">Agent Nodes</h3>
            </div>
            <div className="py-2">
              {agentNodes.map((node) => (
                <motion.div
                  key={node.id}
                  className={`px-4 py-2 border-l-2 cursor-pointer ${
                    selectedNode.id === node.id
                      ? 'border-[#00B0FF] bg-[#00B0FF] bg-opacity-10'
                      : 'border-transparent hover:bg-background-surface'
                  }`}
                  onClick={() => setSelectedNode(node)}
                  whileHover={{ x: 2 }}
                  transition={{ duration: 0.1 }}
                >
                  <div className="flex items-center">
                    {node.icon}
                    <span className="text-sm font-medium">{node.name}</span>
                  </div>
                  {node.description && (
                    <p className="text-xs text-gray-400 mt-1">{node.description}</p>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
          
          {/* Log stream */}
          <div className="flex-grow flex flex-col">
            <div 
              className="flex-grow overflow-y-auto p-4 font-mono text-sm bg-background-dark"
              style={{ maxHeight: 'calc(100% - 2rem)' }}
            >
              <AnimatePresence>
                {filteredLogs.map((log) => (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mb-2 pb-2 border-b border-gray-800"
                  >
                    <div className="flex items-start">
                      <div className="mt-1 mr-2">
                        <StatusIcon status={log.status} />
                      </div>
                      <div>
                        <div className="flex items-center text-xs mb-1">
                          <span className="text-gray-400">{formatTime(log.timestamp)}</span>
                          <span className={`ml-2 px-1.5 py-0.5 rounded text-xs ${
                            log.status === 'info' ? 'bg-[#00B0FF] bg-opacity-20 text-[#00B0FF]' :
                            log.status === 'processing' ? 'bg-[#FFB300] bg-opacity-20 text-[#FFB300]' :
                            log.status === 'success' ? 'bg-[#00E676] bg-opacity-20 text-[#00E676]' :
                            'bg-[#FF1744] bg-opacity-20 text-[#FF1744]'
                          }`}>
                            {log.agent}
                          </span>
                        </div>
                        <div className={`${
                          log.status === 'error' ? 'text-[#FF1744]' : 'text-gray-300'
                        }`}>
                          {log.message}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={logsEndRef} />
            </div>
            <div className="px-4 py-2 border-t border-gray-800 flex justify-between items-center text-xs">
              <span className="text-gray-400">
                {filteredLogs.length} log entries
                {selectedNode.id !== 'all' && ` for ${selectedNode.name}`}
              </span>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="autoscroll"
                  checked={autoscroll}
                  onChange={() => setAutoscroll(!autoscroll)}
                  className="mr-2"
                />
                <label htmlFor="autoscroll" className="text-gray-400">Auto-scroll</label>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}