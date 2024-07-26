import React, { useEffect, useState } from 'react';
import { MainContainer, ChatContainer, MessageList, Message, MessageInput } from '@chatscope/chat-ui-kit-react';
import { useForm, Controller } from 'react-hook-form';
import { Button } from '@mui/material'; 
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
    const selectedModel = models.find((model) => model.modelName === data.model);
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
        options={models.map((model) => model.modelName)}
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
        setModels(response.data);
      } catch (error) {
        setModels([{'modelId': 'a2414', 'modelName': 'Nir Model', 'modelMaxSeqLen': 8192}]);
        console.error('Error fetching model data:', error);
      }
    };

    fetchModels();

    return () => {
      // Stop inference on component unmount
      axios.get('/api/backend/stopInference').catch((error) => console.error('Error stopping inference:', error));
    };
  }, []);

  const handleModelSelect = async (selectedModel: ModelData) => {
    if (selectedModel) {
      setSelectedModel(selectedModel);
      setLoadingModel(true);

      try {
        await axios.post('/api/backend/loadModel', { modelId: selectedModel.modelId });
      } catch (error) {
        console.error('Error loading model:', error);
      } finally {
        setLoadingModel(false);
      }
    }
  };

  const handleSend = async (text: string) => {
    if (!selectedModel) return;
    const userMessage: ChatMessage = {
      id: new Date().toISOString(),
      text,
      sender: 'user',
    };

    setMessages([...messages, userMessage]);
    setIsStreaming(true);

    try {
      const queryParams = new URLSearchParams({ prompt: text }).toString();
      const response = await fetch(`http://instructlab.mhsb7.sandbox2006.opentlc.com:443/api/backend/inference?${queryParams}`, {
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
  
      let done = false;
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value, { stream: !doneReading });
  
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          const lastMessage = updatedMessages[updatedMessages.length - 1];
          if (lastMessage && lastMessage.sender === 'bot') {
            lastMessage.text += chunkValue;
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
            <MainContainer style={{height: '90%', padding: '10px', marginTop: '20px'}}>
              <ChatContainer>
                <MessageList>
                  {messages.map((message, index) => (
                    <Message
                      key={message.id}
                      model={{
                        message: message.text,
                        sentTime: 'just now',
                        sender: message.sender === 'user' ? 'You' : 'Bot',
                        direction: message.sender === 'user' ? 'outgoing' : 'incoming',
                        position: getPosition(index, message.sender),
                      }}
                    />
                  ))}
                </MessageList>
                <MessageInput placeholder="Type your message here..." onSend={handleSend} disabled={loadingModel || isStreaming} />
              </ChatContainer>
            </MainContainer>
          </>): (<ModelSelection models={models} onSelectModel={handleModelSelect} />)
        }
    </div>
  );
};

export default ChatComponent;
