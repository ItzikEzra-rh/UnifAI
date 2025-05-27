import { Card, CardContent } from "@/components/ui/card";
import { motion } from "framer-motion";
import { useState } from "react";

interface PipelineVisualizerProps {
  title: string;
}

export default function PipelineVisualizer({ title }: PipelineVisualizerProps) {
  const [activeTimeframe, setActiveTimeframe] = useState<'today' | 'week' | 'month'>('month');
  
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-heading font-semibold text-lg">{title}</h2>
        <div className="flex items-center space-x-2">
          <button 
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              activeTimeframe === 'today'
                ? 'bg-primary bg-opacity-20 text-primary'
                : 'bg-background-card hover:bg-opacity-80 text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTimeframe('today')}
          >
            Today
          </button>
          <button 
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              activeTimeframe === 'week'
                ? 'bg-primary bg-opacity-20 text-primary'
                : 'bg-background-card hover:bg-opacity-80 text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTimeframe('week')}
          >
            Week
          </button>
          <button 
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              activeTimeframe === 'month'
                ? 'bg-primary bg-opacity-20 text-primary'
                : 'bg-background-card hover:bg-opacity-80 text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTimeframe('month')}
          >
            Month
          </button>
        </div>
      </div>

      <Card className="bg-background-card shadow-card border-gray-800">
        <CardContent className="p-5">
          <div className="h-64 w-full relative">
            <svg className="w-full h-full" viewBox="0 0 800 200">
              {/* Background Grid */}
              <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#2A2A2A" strokeWidth="1"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
              
              {/* Data Flow Paths */}
              <motion.path 
                d="M 50 100 C 150 100, 200 50, 300 50 C 400 50, 450 100, 550 100 C 650 100, 700 150, 750 150" 
                fill="none" 
                stroke="var(--primary)" 
                strokeWidth="3" 
                strokeOpacity="0.7"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 2 }}
                strokeDasharray="10"
                className="pipeline-path"
              />
              
              <motion.path 
                d="M 50 150 C 150 150, 200 120, 300 120 C 400 120, 450 170, 550 170 C 650 170, 700 100, 750 100" 
                fill="none" 
                stroke="var(--secondary)" 
                strokeWidth="3" 
                strokeOpacity="0.7"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 2, delay: 0.3 }}
                strokeDasharray="10"
                className="pipeline-path"
              />
              
              <motion.path 
                d="M 50 50 C 150 50, 200 80, 300 80 C 400 80, 450 30, 550 30 C 650 30, 700 60, 750 60" 
                fill="none" 
                stroke="var(--accent)" 
                strokeWidth="3" 
                strokeOpacity="0.7"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 2, delay: 0.6 }}
                strokeDasharray="10"
                className="pipeline-path"
              />
              
              {/* Data Source Nodes */}
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 }}
              >
                <circle cx="50" cy="100" r="8" fill="var(--primary)" />
                <text x="50" y="85" textAnchor="middle" fill="white" fontSize="10">Jira</text>
              </motion.g>
              
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8 }}
              >
                <circle cx="50" cy="150" r="8" fill="var(--secondary)" />
                <text x="50" y="165" textAnchor="middle" fill="white" fontSize="10">Slack</text>
              </motion.g>
              
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.1 }}
              >
                <circle cx="50" cy="50" r="8" fill="var(--accent)" />
                <text x="50" y="35" textAnchor="middle" fill="white" fontSize="10">Docs</text>
              </motion.g>
              
              {/* Processing Nodes */}
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.2 }}
              >
                <circle cx="300" cy="50" r="10" fill="#1E1E1E" stroke="var(--primary)" strokeWidth="2" />
                <text x="300" y="35" textAnchor="middle" fill="white" fontSize="10">Extraction</text>
              </motion.g>
              
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.4 }}
              >
                <circle cx="300" cy="120" r="10" fill="#1E1E1E" stroke="var(--secondary)" strokeWidth="2" />
                <text x="300" y="140" textAnchor="middle" fill="white" fontSize="10">Chunking</text>
              </motion.g>
              
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.6 }}
              >
                <circle cx="300" cy="80" r="10" fill="#1E1E1E" stroke="var(--accent)" strokeWidth="2" />
                <text x="300" y="95" textAnchor="middle" fill="white" fontSize="10">Parsing</text>
              </motion.g>
              
              {/* Embedding Nodes */}
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.8 }}
              >
                <circle cx="550" cy="100" r="10" fill="#1E1E1E" stroke="var(--primary)" strokeWidth="2" />
                <text x="550" y="120" textAnchor="middle" fill="white" fontSize="10">Embedding</text>
              </motion.g>
              
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 2.0 }}
              >
                <circle cx="550" cy="170" r="10" fill="#1E1E1E" stroke="var(--secondary)" strokeWidth="2" />
                <text x="550" y="190" textAnchor="middle" fill="white" fontSize="10">Embedding</text>
              </motion.g>
              
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 2.2 }}
              >
                <circle cx="550" cy="30" r="10" fill="#1E1E1E" stroke="var(--accent)" strokeWidth="2" />
                <text x="550" y="50" textAnchor="middle" fill="white" fontSize="10">Embedding</text>
              </motion.g>
              
              {/* Storage Nodes */}
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 2.4 }}
              >
                <circle cx="750" cy="150" r="8" fill="var(--primary)" />
                <text x="750" y="165" textAnchor="middle" fill="white" fontSize="10">Vector DB</text>
              </motion.g>
              
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 2.6 }}
              >
                <circle cx="750" cy="100" r="8" fill="var(--secondary)" />
                <text x="750" y="115" textAnchor="middle" fill="white" fontSize="10">Vector DB</text>
              </motion.g>
              
              <motion.g
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 2.8 }}
              >
                <circle cx="750" cy="60" r="8" fill="var(--accent)" />
                <text x="750" y="75" textAnchor="middle" fill="white" fontSize="10">Vector DB</text>
              </motion.g>

              {/* Animated Data Particles */}
              <motion.circle 
                cx="50" cy="100" r="3" fill="white" 
                animate={{ 
                  cx: [50, 300, 550, 750],
                  cy: [100, 50, 100, 150],
                }} 
                transition={{ 
                  duration: 8, 
                  repeat: Infinity,
                  ease: "linear"
                }}
                style={{ opacity: 0.8 }}
              />
              
              <motion.circle 
                cx="50" cy="150" r="3" fill="white" 
                animate={{ 
                  cx: [50, 300, 550, 750],
                  cy: [150, 120, 170, 100],
                }} 
                transition={{ 
                  duration: 12, 
                  repeat: Infinity,
                  ease: "linear",
                  delay: 2
                }}
                style={{ opacity: 0.8 }}
              />
              
              <motion.circle 
                cx="50" cy="50" r="3" fill="white" 
                animate={{ 
                  cx: [50, 300, 550, 750],
                  cy: [50, 80, 30, 60],
                }} 
                transition={{ 
                  duration: 10, 
                  repeat: Infinity,
                  ease: "linear",
                  delay: 5
                }}
                style={{ opacity: 0.8 }}
              />
            </svg>
            
            <div className="absolute bottom-2 left-2 flex items-center space-x-4 text-xs">
              <div className="flex items-center">
                <span className="w-2 h-2 rounded-full bg-primary mr-1"></span>
                <span className="text-gray-400">Jira</span>
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 rounded-full bg-secondary mr-1"></span>
                <span className="text-gray-400">Slack</span>
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 rounded-full bg-accent mr-1"></span>
                <span className="text-gray-400">Documents</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
