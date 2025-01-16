import { Box, Divider, Drawer, IconButton, Slider, Tooltip, Typography } from "@mui/material"
import { useTable, useSortBy, Column } from 'react-table';
import ChatHistory, { HistoryChat } from "./ChatHistory"
import { ModelData } from "../types/constants";
import React from "react";
import NewChat from './NewChat.png'; 
import UnloadModal from './UnloadModal.png'; 
import ViewHeadlineIcon from '@mui/icons-material/ViewHeadline';
import { ChatMessage } from "./ChatContainer";
import { title } from "process";

interface ChatSidebarProps {
  drawerOpen: boolean;
  setDrawerOpen: (drawerOpen: boolean) => void;
  data: ModelData[];
  temperature: number;
  setTemperature: (temperature: number) => void;
  isStreaming: boolean;
  clearChat: () => void;
  unloadModel: () => void;
  handleChatSelect: (chatId: string, chatMessages: ChatMessage[]) => Promise<void>;
  currentChatId: string;
  historyChats: HistoryChat[];
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({drawerOpen, setDrawerOpen, data, temperature, setTemperature, 
                                                        isStreaming, clearChat, unloadModel, handleChatSelect, currentChatId, historyChats}) => {
  const handleTemperatureChange = (event: Event, newValue: number | number[]) => {
    setTemperature(newValue as number);
  };

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };
    
  const ChatToolTip = ({ data }: { data: ModelData[] }) => {
    const columnMap = [
      {title: "Model Name", value: "modelName"},
      {title: "Training Name", value: "trainingName"},
      {title: "Model Max Seq Len", value: "modelMaxSeqLen"}
    ]

    return (
      <div className="chat-tooltip">
        {data.map((row, index) => (
          <div key={index}>
            {columnMap.map((column, colIndex) => (
              <div key={colIndex}>
                <strong>{column.title}: </strong> {(row as any)[column.value] || 'N/A'}
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  };

  const TemperatureTool = () => {
    return (
      <div className="temp-slider">
        <Tooltip title={temperatureTooltip} arrow placement="top">
          <Typography id="temperature-slider" variant="caption" gutterBottom style={{ cursor: 'help' }}>
            Temperature: {temperature.toFixed(1)}
          </Typography>
        </Tooltip>
        <Slider
          value={temperature}
          onChange={handleTemperatureChange}
          aria-labelledby="temperature-slider"
          valueLabelDisplay="auto"
          sx={{color: "red"}}
          step={0.1}
          marks
          min={0}
          max={2}
          size="small"
        />
      </div>
    )
  };

  const temperatureTooltip = `In LLM inference, temperature controls response randomness \n\n.
        Low temperature (e.g., 0.1): Yields more focused, predictable outputs by favoring the most likely tokens, ideal for accuracy\n.
        High temperature (e.g., 1.0+): Promotes diversity and creativity by allowing less common tokens, good for generating varied content. However, very high values may lead to incoherence\n.
        Temperature 1.0: Provides balanced responses based on token probabilities without added randomness\n.
        In short, lower temperatures yield precise outputs, while higher temperatures add creativity and variation.`;
    
  return (
    <div>
      <IconButton onClick={toggleDrawer} title="Open Sidebar" sx={{ alignItems: 'center' }}>
        <ViewHeadlineIcon sx={{ color: 'red' }} />
      </IconButton>
      <Drawer className="drawer" variant="persistent" open={drawerOpen} onClose={toggleDrawer}>
        <div style={{ boxSizing: 'border-box' }}>
          <div className="chat-top-buttons">
            <IconButton onClick={toggleDrawer} title="Close Sidebar" sx={{ alignSelf: 'flex-start' }}>
              <ViewHeadlineIcon sx={{ color: 'red' }} />
            </IconButton>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', }}>
              <IconButton title="Start New Chat" onClick={clearChat} disabled={isStreaming}>
                <img src={NewChat} alt="New Chat" style={{ width: 24, height: 24 }}/>
              </IconButton>
              <IconButton title="Unload Model" onClick={unloadModel}>
                <img src={UnloadModal} alt="Unload Model" style={{ width: 24, height: 24 }}/>
              </IconButton>
            </Box>
          </div>
          <Divider orientation="horizontal" flexItem />
          <div className="inner-drawer">
            <ChatToolTip data={data}/>
          </div>
          <Divider orientation="horizontal" flexItem />
          <div className="inner-drawer">
            <TemperatureTool />
          </div>
          <Divider orientation="horizontal" flexItem />
          <div className="inner-drawer">
            <ChatHistory
              isStreaming={isStreaming}
              onChatSelect={handleChatSelect}
              currentChatId={currentChatId}
              historyChats={historyChats}
            />
          </div>
        </div>
      </Drawer>
    </div>
  )
}
