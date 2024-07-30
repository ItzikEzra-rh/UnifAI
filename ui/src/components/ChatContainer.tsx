import React, { useEffect, useState } from 'react';
import { MainContainer, ChatContainer, MessageList, Message, MessageInput } from '@chatscope/chat-ui-kit-react';
import { useForm, Controller } from 'react-hook-form';
import { Button, IconButton, Tooltip  } from '@mui/material'; 
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import StopIcon from '@mui/icons-material/Stop';
import AutorenewIcon from '@mui/icons-material/Replay';
import { FormDropdown } from './FormFields'; // Adjust the import path as needed
import { useTable, useSortBy, Column } from 'react-table';
import {ModelData} from './types/constants'
import ReactLoading from 'react-loading'; // Add this import if using react-loading
import '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import axios from '../http/axiosLLMConfig';
import '../styles.css';

interface FormData {
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
  const { control, handleSubmit, watch } = useForm<FormData>();
  const selectedModel = watch('model'); // Watch the form field for changes

  const handleModelSubmit = (data: FormData) => {
    const selectedModel = models.find((model) => model.trainingName === data.model);
    if (selectedModel) {
      onSelectModel(selectedModel);
    }
  };

  return (
    <form onSubmit={handleSubmit(handleModelSubmit)} className="form-section">
      <FormDropdown
        name="model"
        label="Choose Model"
        control={control}
        errors={{}} // Pass any validation errors here if needed
        options={models.map((model) => model.trainingName)}
      />
      <Button type="submit" variant="contained" color="primary" disabled={!selectedModel} style={{ float: 'right', marginTop: '10px' }}> Load Model</Button>
    </form>
  );
};

const ChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [models, setModels] = useState<ModelData[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelData | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [loadingModel, setLoadingModel] = useState(false);

  useEffect(() => {
    // Fetch available models on component mount
    const fetchModels = async () => {
      try {
        const response = await axios.get<ModelData[]>('/api/backend/getModels');
        const transformedData: ModelData[] = response.data.map((item: any) => ({
          modelId: item._id,
          modelName: item.model_name,
          trainingName: item.training_name,
          modelMaxSeqLen: item.context_length,
        }));
        setModels(transformedData);
      } catch (error) {
        console.error('Error fetching model data:', error);
      }
    };

    fetchModels();

    return () => {
      // Stop inference on component unmount
      axios.get('/api/backend/stopInference').catch((error) => console.error('Error stopping inference:', error));
    };
  }, []);

  const unloadModel = () => {
    setSelectedModel(null);
    setMessages([]);
  };
  

  const handleModelSelect = async (selectedModel: ModelData) => {
    if (selectedModel) {
      setSelectedModel(selectedModel);
      setLoadingModel(true);

      try {
        await axios.get('/api/backend/loadModel', {params: { modelId: selectedModel.modelId }});
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
      const formattedText = text.replace(/<br>/g, '\n');

      const queryParams = new URLSearchParams({ prompt: formattedText }).toString();
      const response = await fetch(`http://instructlab.zqwrx.sandbox2350.opentlc.com:443/api/backend/inference?${queryParams}`, {
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

    // Define the default text pattern
    const defaultStartText = 'Write a Robot Test Framework. with the following test cases:\n\n';
    const defaultEndText = '\n\n*** Settings ***:'

    // Prepend the default text to the user's message
    const userMessageText: string = `${defaultStartText}${text}${defaultEndText}`;
    const userMessage: ChatMessage = {
      id: new Date().toISOString(),
      text: userMessageText,
      sender: 'user',
    };

    setMessages([...messages, userMessage]);
    setIsStreaming(true);

    sendQuestion(userMessageText)
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
      await axios.get('/api/backend/stopInference');
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
    <div style={{ height: '100%', border: '1px solid #ccc', padding: '10px' }}>
      {loadingModel ? (
        <div className="loading-overlay">
          {/* You can use a library like react-loading for the spinner */}
          <ReactLoading type="bubbles" color="#000" height={100} width={100} />
        </div>
      ) : selectedModel ? (
          <>
            {/* Custom section for displaying model information */}
            <ChatToolTip/>
            <div style={{ position: 'relative', height: '90%' }}>
              <MainContainer style={{height: '95%', padding: '10px', marginTop: '20px'}}>
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
                        </div>
                      )}
                    </div>
                  ))}
                </MessageList>
                <MessageInput placeholder="Type your message here..." onSend={handleSend} disabled={loadingModel || isStreaming} />
                </ChatContainer>
              </MainContainer>
              <Button variant="contained" color="primary" onClick={unloadModel} style={{ position: 'absolute', bottom: '10px', right: '5px' }}>
                Unload Model
              </Button>
            </div>           
          </>): (<ModelSelection models={models} onSelectModel={handleModelSelect} />)
        }
    </div>
  );
};

export default ChatComponent;
