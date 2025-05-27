import React, { memo, useCallback } from 'react';
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronRight } from "lucide-react";
import { StreamLogEntry } from './types';
import { StatusIndicator } from './StatusIndicator';

interface StreamLogItemProps {
  log: StreamLogEntry;
  messageId: string;
  onToggleExpansion: (messageId: string, nodeId: string) => void;
}

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
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for memo
  const prevLog = prevProps.log;
  const nextLog = nextProps.log;
  
  return (
    prevLog.nodeId === nextLog.nodeId &&
    prevLog.status === nextLog.status &&
    prevLog.message === nextLog.message &&
    prevLog.isExpanded === nextLog.isExpanded &&
    prevProps.messageId === nextProps.messageId
  );
});