import React, { memo, useCallback } from 'react';
import { Message } from './types';
import { StreamLogItem } from './StreamLogItem';

interface StreamLogDisplayProps {
  message: Message;
  onToggleExpansion: (messageId: string, nodeId: string) => void;
}

export const StreamLogDisplay = memo(({ message, onToggleExpansion }: StreamLogDisplayProps) => {
  const memoizedToggleExpansion = useCallback((messageId: string, nodeId: string) => {
    onToggleExpansion(messageId, nodeId);
  }, [onToggleExpansion]);

  if (!message.streamLogs || message.streamLogs.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 space-y-2 w-full">
      {message.streamLogs.map((log) => (
        <StreamLogItem
          key={log.nodeId}
          log={log}
          messageId={message.id}
          onToggleExpansion={memoizedToggleExpansion}
        />
      ))}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for memo - only re-render if streamLogs actually changed
  const prevLogs = prevProps.message.streamLogs || [];
  const nextLogs = nextProps.message.streamLogs || [];
  
  if (prevLogs.length !== nextLogs.length) {
    return false;
  }
  
  // Deep comparison of streamLogs
  for (let i = 0; i < prevLogs.length; i++) {
    const prevLog = prevLogs[i];
    const nextLog = nextLogs[i];
    
    if (
      prevLog.nodeId !== nextLog.nodeId ||
      prevLog.status !== nextLog.status ||
      prevLog.message !== nextLog.message ||
      prevLog.isExpanded !== nextLog.isExpanded
    ) {
      return false;
    }
  }
  
  return true;
});