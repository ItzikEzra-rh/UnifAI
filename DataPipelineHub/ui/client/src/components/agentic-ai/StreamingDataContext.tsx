// StreamingDataContext.tsx
import React, { createContext, useContext, useRef } from 'react';

type NodeStreamState = 'PROGRESS' | 'DONE';

export type NodeEntry = {
  node_name: string;
  stream: NodeStreamState;
  text: string;
};

type StreamingContextType = {
  nodeListRef: React.MutableRefObject<Map<string, NodeEntry>>;
  forceUpdate: () => void;
};

const StreamingDataContext = createContext<StreamingContextType | null>(null);

export const StreamingDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const nodeListRef = useRef<Map<string, NodeEntry>>(new Map());
  const [, setTick] = React.useState(0);

  const forceUpdate = () => setTick(t => t + 1);

  return (
    <StreamingDataContext.Provider value={{ nodeListRef, forceUpdate }}>
      {children}
    </StreamingDataContext.Provider>
  );
};

export const useStreamingData = () => {
  const context = useContext(StreamingDataContext);
  if (!context) throw new Error('useStreamingData must be used within a StreamingDataProvider');
  return context;
};