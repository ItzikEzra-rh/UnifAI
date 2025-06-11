import React, { memo, useCallback } from 'react';
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronRight, Wrench } from "lucide-react";
import { StreamLogEntry, ToolEntry } from './types';
import { StatusIndicator } from './StatusIndicator';

interface StreamLogItemProps {
  log: StreamLogEntry;
  messageId: string;
  onToggleExpansion: (messageId: string, nodeId: string) => void;
}

// Separate component for tool call display
const ToolCallItem = ({ tool }: { tool: ToolEntry }) => (
  <div className="flex items-start space-x-3 p-3 bg-blue-950/30 border border-blue-800/40 rounded-md mb-2 last:mb-0">
    <div className="flex-shrink-0 mt-0.5">
      <Wrench className="h-4 w-4 text-blue-400" />
    </div>
    <div className="flex-1 min-w-0">
      <div className="flex items-center space-x-2 mb-1">
        <span className="text-sm font-medium text-blue-300">
          Tool Calling ({tool.name})
        </span>
      </div>
      <div className="text-sm text-gray-300">
        <span className="text-gray-400">result:</span>{' '}
        <span className="font-mono bg-gray-800/50 px-1.5 py-0.5 rounded text-xs">
          {tool.output}
        </span>
      </div>
    </div>
  </div>
);

ToolCallItem.displayName = 'ToolCallItem';

// Separate component for tools section
const ToolsSection = ({ tools }: { tools: ToolEntry[] }) => {
  if (!tools || tools.length === 0) return null;

  return (
    <div className="px-3 pb-2">
      <div className="mb-2">
        <span className="text-xs font-medium text-blue-400 uppercase tracking-wide">
          Tool Calls ({tools.length})
        </span>
      </div>
      <div className="space-y-2">
        {tools.map((tool, index) => (
          <ToolCallItem key={`${tool.name}-${index}`} tool={tool} />
        ))}
      </div>
    </div>
  );
};

ToolsSection.displayName = 'ToolsSection';

export const StreamLogItem = memo(({ log, messageId, onToggleExpansion }: StreamLogItemProps) => {
  const handleToggle = useCallback(() => {
    onToggleExpansion(messageId, log.nodeId);
  }, [messageId, log.nodeId, onToggleExpansion]);

  const getStatusText = useCallback((status: string) => {
    switch (status) {
      case 'processing': return 'Generating...';
      case 'complete': return 'Complete';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  }, []);

  const hasTools = log.tools && log.tools.length > 0;

  return (
    <div className="border border-gray-700 rounded-lg overflow-hidden w-full">
      <div
        className="flex items-center justify-between p-3 bg-gray-800 cursor-pointer hover:bg-gray-750 transition-colors w-full"
        onClick={handleToggle}
      >
        <div className="flex items-center space-x-2">
          <StatusIndicator status={log.status} />
          <span className="text-sm font-medium text-gray-200">
            {log.nodeName}
          </span>
          <span className="text-xs text-gray-400">
            {getStatusText(log.status)}
          </span>
          {hasTools && (
            <div className="flex items-center space-x-1">
              <Wrench className="h-3 w-3 text-blue-400" />
              <span className="text-xs text-blue-400">
                {log.tools.length} tool{log.tools.length !== 1 ? 's' : ''}
              </span>
            </div>
          )}
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
            {/* Tools Section */}
            {hasTools && (
              <div className="bg-gray-900 border-t border-gray-700 w-full">
                <ToolsSection tools={log.tools} />
              </div>
            )}
            
            {/* Message Section */}
            <div className={`p-3 bg-gray-900 w-full ${hasTools ? '' : 'border-t border-gray-700'}`}>
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
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for memo
  const prevLog = prevProps.log;
  const nextLog = nextProps.log;
  
  // Deep comparison for tools array
  const toolsEqual = (prev: ToolEntry[] = [], next: ToolEntry[] = []) => {
    if (prev.length !== next.length) return false;
    return prev.every((tool, index) => 
      tool.id === next[index]?.id
    );
  };
  
  return (
    prevLog.nodeId === nextLog.nodeId &&
    prevLog.status === nextLog.status &&
    prevLog.message === nextLog.message &&
    prevLog.isExpanded === nextLog.isExpanded &&
    prevProps.messageId === nextProps.messageId &&
    toolsEqual(prevLog.tools, nextLog.tools)
  );
});

StreamLogItem.displayName = 'StreamLogItem';