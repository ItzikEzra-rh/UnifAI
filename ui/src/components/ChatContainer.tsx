import React, { useEffect, useState } from 'react';
import { MainContainer, ChatContainer, MessageList, Message, MessageInput } from '@chatscope/chat-ui-kit-react';
import { useForm, Controller } from 'react-hook-form';
import { Button, IconButton, Tooltip, Stepper, Step, StepButton, Dialog, DialogActions, DialogContent, DialogTitle, TextField } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SaveIcon from '@mui/icons-material/Save';
import StopIcon from '@mui/icons-material/Stop';
import AutorenewIcon from '@mui/icons-material/Replay';
import { FormDropdown } from './FormFields';
import { useTable, useSortBy, Column } from 'react-table';
import {ModelData} from './types/constants'
import ReactLoading from 'react-loading';
import '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import axiosLLM from '../http/axiosLLMConfig';
import axiosBE from '../http/axiosConfig'
import '../styles.css';

interface FormData {
  project: string;
  model: string;
}

interface ModelSelectionProps {
  models: ModelData[];
  onSelectModel: (model: ModelData) => void;
}

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

const ModelSelection: React.FC<ModelSelectionProps> = ({ models, onSelectModel }) => {
  const { control, handleSubmit, watch, setValue } = useForm<FormData>();
  const [activeStep, setActiveStep] = useState<number>(0);
  const [steps, setSteps] = useState<any[]>([]);
  const [filteredModels, setFilteredModels] = useState<ModelData[]>(models);
  const [selectedDropDownMenu, setSelectedDropDownMenu] = useState<ModelData | null>(null);
  
  const selectedProject = watch('project');
  const selectedModel = watch('model'); // Watch the form field for changes

  const handleStepClick = (index: number) => {
    setActiveStep(index);
  };

  const handleModelSubmit = (data: FormData) => {
    const selectedModel = models.find((model) => model.trainingName === data.model);
    if (selectedModel) {
      onSelectModel(selectedModel);
    }
  };

  const handleProjectSelection = (selectedProject: string) => {
    setValue('model', ''); // Reset the model selection when project changes
    const filtered = models.filter((model) => model.project === selectedProject);
    setFilteredModels(filtered);
    setSelectedDropDownMenu(null); // Reset model selection when project changes
  };

  const handleModelSelection = (selectedItem: string) => {
    const foundItem = models.find((model) => model.trainingName === selectedItem);
    if (foundItem) {
      setActiveStep(0)
      setSteps([])
      setSelectedDropDownMenu(foundItem);

      if (foundItem.finetuneSteps && foundItem.finetuneSteps.length > 0) {
        setSteps([{ label: foundItem.finetuneSteps[0].base_model },
                    ...foundItem.finetuneSteps.map((step, idx) => ({
                      label: foundItem.finetuneSteps && foundItem.finetuneSteps[idx+1]? `${foundItem.finetuneSteps[idx+1]?.base_model}` : `${foundItem.modelName}`,
                      details: step,
                    }))]);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(handleModelSubmit)} className="form-section">
      <FormDropdown
        name="project"
        label="Choose Project"
        control={control}
        errors={{}}
        options={Array.from(new Set(models.map((model) => model.project)))}
        onSelect={handleProjectSelection}
      />
      <FormDropdown
        name="model"
        label="Choose Model"
        control={control}
        errors={{}}
        options={filteredModels.map((model) => model.trainingName)}
        onSelect={handleModelSelection}
      />
      {selectedDropDownMenu && (
        <div className="model-details" style={{ marginTop: '20px' }}>
          <h4>Selected Model Details</h4>
          {selectedDropDownMenu.project && <p>Project: {selectedDropDownMenu.project}</p>}
          {selectedDropDownMenu.modelMaxSeqLen && <p>Context Length: {selectedDropDownMenu.modelMaxSeqLen}</p>}
          {selectedDropDownMenu.modelName && <p>Model Name: {selectedDropDownMenu.modelName}</p>}
          {selectedDropDownMenu.modelType && <p>Model Type: {selectedDropDownMenu.modelType}</p>}
          {selectedDropDownMenu.checkpoint && <p>Checkpoint: {selectedDropDownMenu.checkpoint}</p>}
          <br/><br/>
          {steps.length > 0 && (
            <div className="finetune-steps">
              <h4>Finetune Evolution</h4>
              <div>
                <Stepper activeStep={activeStep} alternativeLabel nonLinear>
                  {steps.map((step, index) => (
                    <Step key={index}>
                      <StepButton onClick={() => handleStepClick(index)}>
                        {step.label}
                      </StepButton>
                    </Step>
                  ))}
                </Stepper>

                {activeStep !== null && steps[activeStep].details && (
                  <div className="step-details-container">
                    {/* <pre>{JSON.stringify(steps[activeStep].details, null, 2)}</pre> */}
                    <ul className="step-details-list">
                      {Object.entries(steps[activeStep].details).map(([key, value]) => (
                        <li key={key}>
                          <strong>{key}:</strong> {String(value)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
      <Button type="submit" variant="contained" color="primary" disabled={!selectedModel || !selectedProject} style={{ float: 'right', marginTop: '10px' }}> Load Model</Button>
    </form>
  );
};

const ChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [models, setModels] = useState<ModelData[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelData | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [loadingModel, setLoadingModel] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [promptName, setPromptName] = useState<string>('');
  const [messageToSave, setMessageToSave] = useState<string>('');

  useEffect(() => {
    // Fetch available models on component mount
    const fetchModels = async () => {
      try {
        const response = await axiosLLM.get<ModelData[]>('/api/backend/getModels');
        const transformedData: ModelData[] = response.data.map((item: any) => ({
          modelId: item._id,
          modelName: item.name,
          trainingName: item.name,
          modelMaxSeqLen: item.context_length,
          modelType: item.model_type,
          project: item.project,
          checkpoint: item?.checkpoint,
          finetuneSteps: item?.finetune_steps,
          promptTemplate: item?.prompt_template,
        }));
        setModels(transformedData);
      } catch (error) {
        console.error('Error fetching model data:', error);
      }
    };

    fetchModels();

    return () => {
      // Stop inference on component unmount
      axiosLLM.get('/api/backend/stopInference').catch((error) => console.error('Error stopping inference:', error));
    };
  }, []);

  const unloadModel = () => {
    handleStop();
    setSelectedModel(null);
    setMessages([]);
  };
  

  const handleModelSelect = async (selectedModel: ModelData) => {
    if (selectedModel) {
      setSelectedModel(selectedModel);
      setLoadingModel(true);

      try {
        await axiosLLM.get('/api/backend/loadModel', {params: { modelId: selectedModel.modelId }});
      } catch (error) {
        console.error('Error loading model:', error);
      } finally {
        setLoadingModel(false);
      }
    }
  };

  const sendQuestion = async (text: string) => {
    try {
      // Replace <br> tags with \n in the input text
      let formattedText = text.replace(/<br>/g, '\n');
      formattedText = formattedText.replace(/<div>/g, '');
      formattedText = formattedText.replace(/<\/div>/g, '\n');
      formattedText = formattedText.replace(/&nbsp;/g, '');

      const queryParams = new URLSearchParams({ prompt: formattedText }).toString();
      const response = await fetch(`http://instructlab.sdn5r.sandbox429.opentlc.com:443/api/backend/inference?${queryParams}`, {
        method: 'GET',
      });
  
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      if (!response.body) throw new Error('ReadableStream not supported!');
  
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let botMessage: ChatMessage = {
        id: new Date().toISOString(),
        text: '',
        sender: 'bot',
      };
  
      setMessages((prevMessages) => [...prevMessages, botMessage]);
  
      let accumulatedText = '';
      while (true) {
        const { value, done: doneReading } = await reader.read();
        if (doneReading) break;
        let chunkValue = decoder.decode(value, { stream: true });
        chunkValue = chunkValue.replace(/<s>/g, '');
        accumulatedText += chunkValue;
  
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          const lastMessage = updatedMessages[updatedMessages.length - 1];
          if (lastMessage && lastMessage.sender === 'bot') {
            lastMessage.text = accumulatedText;
          }
          return updatedMessages;
        });
      }
    } catch (error) {
      console.error('Error communicating with chat API', error);
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          id: new Date().toISOString(),
          text: 'An error occurred while processing your request.',
          sender: 'bot',
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  }

  const handleSend = async (text: string) => {
    if (!selectedModel) return;

    // Use the prompt template from the selected model
    const startTag = selectedModel.promptTemplate?.user_tag || '';
    const endTag = selectedModel.promptTemplate?.end_tag || '';
    const assistantTag = selectedModel.promptTemplate?.assistant_tag || '';

    // Construct the message using the dynamic prompt template
    const userMessageText = `${startTag}${text}${endTag} ${assistantTag}`;
    const userMessage: ChatMessage = {
      id: new Date().toISOString(),
      text: userMessageText,
      sender: 'user',
    };

    setMessages([...messages, userMessage]);
    setIsStreaming(true);

    sendQuestion(userMessageText)
  };

  const handleSaveClick = (messageText: string) => {
    setMessageToSave(messageText); 
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setPromptName('');
  };

  const handlePromptNameChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPromptName(event.target.value); // Update prompt name as user types
  };

  const handleSavePrompt = async () => {
    if (!promptName) return; // Do nothing if no prompt name is provided
    if (!selectedModel) return;
  
    try {
      const payload = {
        modelId: selectedModel.modelId,
        trainingName: selectedModel.trainingName,
        promptText: messageToSave, // Message stored in state
        promptName: promptName,   // Name entered by the user
      };
      await axiosBE.post('/api/backend/savePrompt', payload);
      console.log('Prompt saved successfully');
      handleModalClose(); // Close the modal after saving
    } catch (error) {
      console.error('Error saving prompt:', error);
    }
  };

  const regenerateResponse = async () => {
    const lastUserMessage = messages.slice().reverse().find(msg => msg.sender === 'user');
    if (!lastUserMessage) return;

    setIsStreaming(true);
    setMessages(prevMessages => [
      ...prevMessages,
      { ...lastUserMessage, id: new Date().toISOString() }, // Re-add the user's message
    ]);

    sendQuestion(lastUserMessage.text)
  };

  const handleStop = async () => {
    try {
      await axiosLLM.get('/api/backend/stopInference');
      setIsStreaming(false);
    } catch (error) {
      console.error('Error stopping inference:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getPosition = (index: number, sender: string): 'normal' | 'first' | 'last' | 'single' => {
    const previousMessage = messages[index - 1];
    const nextMessage = messages[index + 1];
  
    switch (true) {
      case previousMessage?.sender !== sender && nextMessage?.sender !== sender: return 'single';
      case previousMessage?.sender !== sender: return 'first';
      case nextMessage?.sender !== sender: return 'last'; 
      default: return 'normal';
    }
  };

  const columns: Column<ModelData>[] = React.useMemo(
    () => [
      { Header: 'Model Name', accessor: 'modelName' },
      { Header: 'Training Name', accessor: 'trainingName' },
      { Header: 'Model Max Seq Len', accessor: 'modelMaxSeqLen' },
    ],
    []
  );

  const ChatToolTip = () => 
      <table {...getTableProps()} className="forms-table">
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map((column: any) => (
                <th {...column.getHeaderProps(column.getSortByToggleProps())}>
                  {column.render('Header')}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.map(row => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()}>
                {row.cells.map(cell => (
                  <td
                    {...cell.getCellProps()}
                    className="table-cell"
                    onMouseEnter={(e) => {
                      const columnIndex = cell.column.id;
                      const cells = document.querySelectorAll(`td[data-column-id="${columnIndex}"]`);
                      cells.forEach(cell => (cell as HTMLElement).style.backgroundColor = 'rgba(46, 120, 199, 0.2)');
                    }}
                    onMouseLeave={(e) => {
                      const columnIndex = cell.column.id;
                      const cells = document.querySelectorAll(`td[data-column-id="${columnIndex}"]`);
                      cells.forEach(cell => (cell as HTMLElement).style.backgroundColor = '');
                    }}
                    data-column-id={cell.column.id}
                  >
                    {cell.render('Cell')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>

  const data = React.useMemo(() => selectedModel ? [selectedModel] : [], [selectedModel]);
  const {getTableProps, getTableBodyProps, headerGroups, rows, prepareRow} = useTable({ columns, data }, useSortBy);

  return (
    <div style={{ height: '100%', border: '1px solid #ccc', padding: '10px', position: 'relative' }}>
      {loadingModel ? (
        <div className="loading-overlay">
          {/* You can use a library like react-loading for the spinner */}
          <ReactLoading type="bubbles" color="#000" height={100} width={100} />
        </div>
      ) : selectedModel ? (
          <>
            {/* Custom section for displaying model information */}
            <ChatToolTip/>
            <Button variant="contained" color="primary" onClick={unloadModel} style={{ position: 'absolute', top: '10px', right: '10px' }}>
                Unload Model
            </Button>
            <div style={{ position: 'relative', height: '80vh' }}>
              <MainContainer style={{padding: '10px', marginTop: '20px'}}>
                <ChatContainer>
                <MessageList>
                  {messages.map((message, index) => (
                    <div key={message.id} style={{ position: 'relative', paddingBottom: '40px' }}>
                      <Message
                        model={{
                          message: message.text, // Ensure message is a string
                          sentTime: 'just now',
                          sender: message.sender === 'user' ? 'You' : 'Bot',
                          direction: message.sender === 'user' ? 'outgoing' : 'incoming',
                          position: getPosition(index, message.sender),
                        }}
                      />
                      {message.sender === 'bot' && (
                        <div style={{ position: 'absolute', bottom: '5px', left: '5px', display: 'flex', gap: '5px' }}>
                          <Tooltip title="Copy">
                            <IconButton onClick={() => copyToClipboard(message.text)} size="small">
                              <ContentCopyIcon />
                            </IconButton>
                          </Tooltip>
                          {isStreaming && (
                            <Tooltip title="Stop">
                              <IconButton onClick={handleStop} size="small">
                                <StopIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          {!isStreaming && (
                            <Tooltip title="Regenerate">
                              <IconButton
                                onClick={regenerateResponse}
                                size="small"
                              >
                                <AutorenewIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Save">
                            <IconButton onClick={() => handleSaveClick(message.text)} size="small">
                              <SaveIcon />
                            </IconButton>
                          </Tooltip>
                        </div>
                      )}
                    </div>
                  ))}
                </MessageList>
                <MessageInput placeholder="Type your message here..." onSend={handleSend} disabled={loadingModel || isStreaming} />
                </ChatContainer>
              </MainContainer>
              <Dialog open={isModalOpen}
                      onClose={handleModalClose}
                      PaperProps={{
                        style: { width: '50%', margin: '0 auto' }, // Custom width set to 50% and centered horizontally
                      }}>
                  <DialogTitle>Save Prompt</DialogTitle>
                  <DialogContent>
                    <TextField autoFocus margin="dense" label="Prompt Name" type="text" fullWidth variant="standard" value={promptName} onChange={handlePromptNameChange}/>
                  </DialogContent>
                  <DialogActions>
                    <Button onClick={handleModalClose} color="secondary">Cancel</Button>
                    <Button onClick={handleSavePrompt} color="primary">Save</Button>
                  </DialogActions>
                </Dialog>
            </div>           
          </>): (<ModelSelection models={models} onSelectModel={handleModelSelect} />)
        }
    </div>
  );
};

export default ChatComponent;
