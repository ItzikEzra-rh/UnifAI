import React, { useState, useEffect } from 'react';
import axiosBE from '../../http/axiosConfig';
import { Box, Divider, Drawer, IconButton, Slider, Tooltip, Typography, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Select, FormControl, InputLabel, Button } from "@mui/material"
import { useTable, useSortBy, Column } from 'react-table';
import ChatHistory, { HistoryChat } from "./ChatHistory"
import { ModelData } from "../types/constants";
import NewChat from '../../assets/NewChat.png'; 
import UnloadModal from '../../assets/UnloadModal.png'; 
import ViewHeadlineIcon from '@mui/icons-material/ViewHeadline';
import { ChatMessage } from "./ChatContainer";

interface ChatSidebarProps {
  drawerOpen: boolean;
  setDrawerOpen: (drawerOpen: boolean) => void;
  selectedModel: ModelData;
  data: ModelData[];
  temperature: number;
  setTemperature: (temperature: number) => void;
  isStreaming: boolean;
  clearChat: () => void;
  unloadModel: () => void;
  unloadingModel: boolean;
  handleChatSelect: (chatId: string, chatMessages: ChatMessage[]) => Promise<void>;
  currentSessionId: string;
  historyChats: HistoryChat[];
  setHistoryChats: (historyChats: HistoryChat[]) => void;
  setSelectedPackages: (selectedPackages: string[]) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({drawerOpen, setDrawerOpen, selectedModel, data, temperature, setTemperature, 
                                                        isStreaming, clearChat, unloadModel, unloadingModel, handleChatSelect, currentSessionId, historyChats, setHistoryChats,
                                                        setSelectedPackages}) => {
  const [packagesNamesList, setPackagesNamesList] = useState<string[]>([]);
  const [firstSelectedPackage, setFirstSelectedPackage] = useState<string | null>(null);
  const [secondSelectedPackage, setSecondSelectedPackage] = useState<string | null>(null);  
  const [packageSelectionModal, setPackageSelectionModal] = useState(false);

  const [modelId, projectName, isPackageSelectionRagEnabled] = [selectedModel.modelId, selectedModel.project, selectedModel.isPackageSelectionRagEnabled];

  useEffect(() => {
    const fetchPackages = async () => {
      try {
        const response = await axiosBE.post('/api/rag/packagesNamesList', { modelId, projectName });
        setPackagesNamesList(response.data.result || []);
        handlePackageSelection()
      } catch (error) {
        console.error('Error fetching package names:', error);
      }
    };
    if (isPackageSelectionRagEnabled && packagesNamesList.length > 0) {
      fetchPackages();
    }
  }, [modelId, projectName]);

  const handlePackageSelection = () => {
    setFirstSelectedPackage(null);
    setSecondSelectedPackage(null);
    setPackageSelectionModal((prevState) => !prevState)
  }

  const handlePackageSelectionSave = () => {
    let selectedPackages: string[] = [firstSelectedPackage, secondSelectedPackage].filter((ele): ele is string => ele !== null)
    setPackageSelectionModal(false);
    setSelectedPackages(selectedPackages)
  }

  const clearChatWithPackageSelection = () => {
    clearChat()
    if (isPackageSelectionRagEnabled && packagesNamesList.length > 0) {
      handlePackageSelection();
    }
  }

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
      <Drawer className="drawer" variant="persistent" open={drawerOpen} >
        <div style={{ boxSizing: 'border-box' }}>
          <div className="chat-top-buttons">
            <IconButton onClick={toggleDrawer} title="Close Sidebar" sx={{ alignSelf: 'flex-start' }}>
              <ViewHeadlineIcon sx={{ color: 'red' }} />
            </IconButton>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', }}>
              <IconButton title="Start New Chat" onClick={clearChatWithPackageSelection} disabled={isStreaming}>
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
              modelId={modelId}
              isStreaming={isStreaming}
              onChatSelect={handleChatSelect}
              currentSessionId={currentSessionId}
              historyChats={historyChats}
              setHistoryChats={setHistoryChats}
              clearChat={clearChat}
              unloadingModel={unloadingModel}
            />
          </div>
        </div>
      </Drawer>

      {/* Package Selection Modal */}
      <Dialog open={packageSelectionModal} onClose={handlePackageSelection}>
        <DialogTitle>Select Up to 2 Packages</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Select the package under which the new test might be implemented, or choose relevant reference packages. 
            This helps improve the model's context, leading to more accurate and relevant test generation.  
            If you prefer to skip this step, you can simply click "Skip".
          </Typography>

          <FormControl fullWidth margin="normal">
            <InputLabel id="package1-label">First Package</InputLabel>
            <Select
              labelId="package1-label"
              value={firstSelectedPackage}
              onChange={(e) => setFirstSelectedPackage(e.target.value)}
              displayEmpty
            >
              <MenuItem value="" disabled>Select a package</MenuItem>
              {packagesNamesList
                .filter((pkg) => pkg !== secondSelectedPackage)
                .map((pkg) => (
                  <MenuItem key={pkg} value={pkg}>
                    {pkg}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>

          <FormControl fullWidth margin="normal">
            <InputLabel id="package2-label">Second Package</InputLabel>
            <Select
              labelId="package2-label"
              value={secondSelectedPackage}
              onChange={(e) => setSecondSelectedPackage(e.target.value)}
              displayEmpty
            >
              <MenuItem value="" disabled>Select a package</MenuItem>
              {packagesNamesList
                .filter((pkg) => pkg !== firstSelectedPackage)
                .map((pkg) => (
                  <MenuItem key={pkg} value={pkg}>
                    {pkg}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handlePackageSelection} sx={{ color: 'black' }}>Skip</Button>
          <Button disabled={!(firstSelectedPackage || secondSelectedPackage)} onClick={handlePackageSelectionSave} color="primary">Save</Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}
