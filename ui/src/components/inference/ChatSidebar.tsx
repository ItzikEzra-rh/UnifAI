import { Box, Button, Divider, Drawer, IconButton, Slider, Tooltip, Typography } from "@mui/material"
import { useTable, useSortBy, Column } from 'react-table';
import ChatHistory from "./ChatHistory"
import { ModelData } from "../types/constants";
import React, { useState } from "react";
import MyCustomIcon from './myCustomIcon.png'; // Import your custom SVG icon
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import HistoryIcon from '@mui/icons-material/History';
import ViewHeadlineIcon from '@mui/icons-material/ViewHeadline';

interface ChatSidebarProps {
  drawerOpen: boolean;
  setDrawerOpen: any;
  data: any;
  temperature: any;
  handleTemperatureChange: any;
  clearChat: any;
  unloadModel: any;
  isStreaming: any;
  handleChatSelect: any;
  currentChatId: any;
  historyChats: any;
}



export const ChatSidebar: React.FC<ChatSidebarProps> = ({ drawerOpen, setDrawerOpen, data, temperature, 
    handleTemperatureChange, clearChat, unloadModel, isStreaming, handleChatSelect, currentChatId, historyChats}) => {
      

      const toggleDrawer = () => {
        setDrawerOpen(!drawerOpen);
      };
    
      const columns: Column<ModelData>[] = React.useMemo(
        () => [
          { Header: 'Model Name', accessor: 'modelName' },
          { Header: 'Training Name', accessor: 'trainingName' },
          { Header: 'Model Max Seq Len', accessor: 'modelMaxSeqLen' },
        ],
        []
      );
      

    const { rows, prepareRow } = useTable(
        { columns, data },
        useSortBy
      );
      
      const ChatToolTip = () => {
        return (
          <div
            style={{
                width: '90%',
                marginTop: '10px',
                padding: '10px',
                marginBottom: '10px',
                fontSize: '13px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                backgroundColor: '#f9f9f9',
            }}
          >
            {rows.map((row) => {
              prepareRow(row);
              return (
                <div key={row.id}>
                  {columns.map((column) => {
                    const cell = row.cells.find((c) => c.column.id === column.accessor);
                    return (
                      <div key={String(column.accessor)}>
                        <strong>{String(column.Header)}: </strong>
                        {cell?.value || 'N/A'}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        );
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
    <Drawer
              variant="persistent"
              open={drawerOpen}
              onClose={toggleDrawer}
              sx={{
                display: 'flex', 
                flexDirection: 'column', 
                '& .MuiPaper-root': {
                    position: 'absolute'
                },
                '& .MuiDrawer-paper': {
                  width: '15%', 
                  boxSizing: 'border-box',
                  overflow: 'visible'
                },
                }}
              >
        <div style={{ boxSizing: 'border-box', margin: '10px' }}>
          <div className="chat-top-buttons">
            <IconButton onClick={toggleDrawer} title="Close Sidebar" sx={{ alignSelf: 'flex-start' }}>
              <ViewHeadlineIcon sx={{ color: 'red' }} />
            </IconButton>

            <Box sx={{ display: 'flex', justifyContent: 'flex-end', }}>
            <IconButton title="Start New Chat" onClick={clearChat} disabled={isStreaming}>
            <img 
              src={MyCustomIcon}
              alt="custom icon" 
              style={{ width: 24, height: 24 }} // Use the style prop here
            />
              {/* <OpenInNewIcon sx={{ color: 'red' }} /> */}
            </IconButton>
            <IconButton title="Unload Model" onClick={unloadModel}>
              <HistoryIcon sx={{ color: 'red' }} />
            </IconButton>
          </Box>
            </div>
          <Divider orientation="vertical" flexItem />
          <ChatToolTip />
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
          <Divider orientation="vertical" flexItem />
          <ChatHistory
            isStreaming={isStreaming}
            onChatSelect={handleChatSelect}
            currentChatId={currentChatId}
            historyChats={historyChats}
          />

          
        </div>
      </Drawer>
      </div>
    )
}
