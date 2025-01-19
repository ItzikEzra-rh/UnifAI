import React, { useEffect, useState, useRef } from 'react';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { MainContainer, ChatContainer, MessageList, Message, MessageInput } from '@chatscope/chat-ui-kit-react';
import { useForm } from 'react-hook-form';
import { Button, IconButton, Tooltip, Stepper, Step, StepButton, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Slider, Typography, Box, Drawer, Divider } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SaveIcon from '@mui/icons-material/Save';
import StopIcon from '@mui/icons-material/Stop';
import StarIcon from '@mui/icons-material/Star';
import AutorenewIcon from '@mui/icons-material/Replay';
import { FormDropdown } from '../shared/FormFields';
import { ModelData } from '../types/constants'
import ReactLoading from 'react-loading';
import '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import axiosLLM, { AXIOS_LLM_IP } from '../../http/axiosLLMConfig';
import axiosBE from '../../http/axiosConfig'
import RatingModal from './RatingModal';
import { HistoryChat } from './ChatHistory';
import { v4 as uuidv4 } from 'uuid';
import '../../styles.css';
import Prism from 'prismjs';
import 'prismjs/themes/prism-okaidia.css';
import { ChatSidebar } from './ChatSidebar';

interface FormData {
  project: string;
  model: string;
}

interface ModelSelectionProps {
  models: ModelData[];
  onSelectModel: (model: ModelData) => void;
}

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

interface RatingData {
  rating: number;
  ratingText: string;
}

const LoadingOverlay: React.FC = () => (
  <div className="loading-overlay">
    <ReactLoading type="bubbles" color="#000" height={100} width={100} />
    <h2 style={{ marginTop: '20px', fontSize: '1.5em', textAlign: 'center', color: '#000' }}>
      Please be patient while we load the requested model. This process may take up to 2 minutes.
    </h2>
  </div>
);

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
          label: foundItem.finetuneSteps && foundItem.finetuneSteps[idx + 1] ? `${foundItem.finetuneSteps[idx + 1]?.base_model}` : `${foundItem.modelName}`,
          details: step,
        }))]);
      }
    }
  };
 
  return (
    <Box style={{padding: '20px'}}>
      <form onSubmit={handleSubmit(handleModelSubmit)}>
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
            <br /><br />
            {steps.length > 0 && (
              <div className="finetune-steps">
                <h4>Finetune Evolution</h4>
                <div>
                  <Stepper activeStep={activeStep} alternativeLabel nonLinear>
                    {steps.map((step, index) => (
                      <Step key={index} className="custom-step">
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
        <div className="form-bottom-button">
          <Button className="end-button" type="submit" variant="contained" color="primary" disabled={!selectedModel || !selectedProject}> Load Model</Button>
        </div>
      </form>
    </Box>
  );
};

const ChatComponent: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>('');
  const sessionIdRef = useRef<string>(''); // Ref to store sessionId immediately
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [models, setModels] = useState<ModelData[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelData | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [loadingModel, setLoadingModel] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [promptName, setPromptName] = useState<string>('');
  const [promptUserLatestMessage, setPromptUserLatestMessage] = useState<string>('');
  const [promptLLMLatestMessage, setPromptLLMLatestMessage] = useState<string>('');
  const [temperature, setTemperature] = useState<number>(0.3);

  const [isRatingModalOpen, setIsRatingModalOpen] = useState<boolean>(false);
  const [messageRatings, setMessageRatings] = useState<{ [key: number]: RatingData }>({});
  const [currentRatingIdx, setCurrentRatingIdx] = useState<number>(-1);
  const [messageIsRated, setMessageIsRated] = useState<{ [key: number]: boolean }>({});

  const [historyChats, setHistoryChats] = useState<HistoryChat[]>([]);
  const [pastChats, setPastChats] = useState<any>(null);
  const [currentChatId, setCurrentChatId] = useState<string>('current');

  useEffect(() => {
    // Check if there's already a session_id in sessionStorage
    let currentSessionId = sessionStorage.getItem('session_id') ?? uuidv4();

    if (!sessionStorage.getItem('session_id')) {
      // Store the new session_id in sessionStorage if it was newly generated
      sessionStorage.setItem('session_id', currentSessionId);
    }

    setSessionId(currentSessionId);
    sessionIdRef.current = currentSessionId; // Update ref immediately


    // Fetch available models on component mount
    const fetchModelsAndCheckLoadedModel = async () => {
      try {
        // Fetch available models
        const modelsResponse = await axiosLLM.get<ModelData[]>('/api/backend/getModels');
        const transformedData: ModelData[] = modelsResponse.data.map((item: any) => ({
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

        // Check for loaded model
        const loadedModelResponse = await axiosLLM.get<string | null>('/api/backend/getLoadedModel');
        const loadedModelId = loadedModelResponse.data;

        if (loadedModelId) {
          const loadedModel = transformedData.find(model => model.modelId === loadedModelId);
          if (loadedModel) {
            setSelectedModel(loadedModel);
            console.log("going to axios now")
            const loadedModelChatsResponse = await axiosLLM.get('/api/backend/getChats', { params: { modelId: loadedModel } });
            console.log(loadedModelChatsResponse)
            // setPastChats(historyChats);
            // const loadedModelChats = loadedModelChatsResponse.data;
            setLoadingModel(false); // Ensure loading state is false as the model is already loaded
          }
        }
      } catch (error) {
        console.error('Error fetching model data:', error);
      }
    };

    fetchModelsAndCheckLoadedModel();

    return () => {
      // Stop inference on component unmount
      axiosLLM.get('/api/backend/stopInference', { params: { sessionId: sessionIdRef.current } }).catch((error) => console.error('Error stopping inference:', error));
      axiosLLM.get('/api/backend/clearChatHistory', { params: { sessionId: sessionIdRef.current } });
    };
  }, []);

  const updateCurrentChat = async (messages: ChatMessage[], sessionId: string, modelId: string | any) => {
    try {
      const formattedMessages = messages.map((message) => ({
        role: message.sender === 'user' ? 'user' : 'assistant',
        content: message.text,
      }));
      const payload = {
        sessionId,
        modelId,
        chat: formattedMessages,
      };
      await axiosBE.post('/api/backend/updateCurrentChat', payload);
    } catch (error) {
      console.error('Error updating chat:', error);
    }
  };

  const unloadModel = () => {
    handleStop();
    handleUnLoad()
    setSelectedModel(null);
    setMessages([]);
  };

  const handleRecentChatSelect = () => {
    // Handle the case once user press on 'Start new chat' & certain 'Recent Chat Item' where currently selected, therefore we should update the messages array of the selected 'Recent Chat Item'
    // Handle the case once user moving between chat histories, we should update the chat that he just moved from with up to date data
    if (messages.length > 0 && currentChatId != "current") {
      const currentHistory = historyChats.map(chat => chat.id == currentChatId && chat.messages.length !== messages.length ? { ...chat, messages: [...messages], timestamp: new Date().toLocaleString() } : chat)
      setHistoryChats(currentHistory)
    }
  }

  const addRecentChat = () => {
    if (messages.length > 0 && currentChatId == "current") {
      const firstUserMessage = messages.find(msg => msg.sender === 'user')?.text || 'New conversation';
      const truncatedMessage = firstUserMessage.length > 40 ? `${firstUserMessage.substring(0, 37)}...` : firstUserMessage;

      const newHistoryChat: HistoryChat = {
        id: `chat-${historyChats.length + 1}`,
        name: `Chat ${historyChats.length + 1}`,
        timestamp: new Date().toLocaleString(),
        messages: [...messages], // Save a copy of current messages
        firstMessage: truncatedMessage
      };

      setHistoryChats(prevHistory => [newHistoryChat, ...prevHistory]);
    }
  }

  const clearChat = async () => {
    try {
      handleRecentChatSelect()
      addRecentChat()
      const response = await axiosLLM.get('/api/backend/clearChatHistory', { params: { sessionId: sessionId } });
      
      // Create a new session_id for the mongoDB chat history
      const newSessionId = uuidv4();
      sessionStorage.setItem('session_id', newSessionId);
      setSessionId(newSessionId);
      sessionIdRef.current = newSessionId;

      setMessages([]);
      setCurrentChatId('current');
    } catch (error) {
      console.error('Error cleaning the chat:', error);
      toast.error('An error occurred while trying to clean the chat.');
    }
  };

  const handleChatSelect = async (chatId: string, chatMessages: ChatMessage[]) => {
    try {
      await axiosLLM.get('/api/backend/clearChatHistory', {
        params: { sessionId: sessionId }
      });

      const newMessages = chatMessages.map(({ id, text, sender }) => ({ content: text, role: sender === 'bot' ? 'assistant' : sender }));
      await axiosLLM.post('/api/backend/loadChatContext', {
        sessionId: sessionId,
        chat: newMessages,
      })
      // Load selected chat messages
      setMessages(chatMessages);
      setCurrentChatId(chatId);
      handleRecentChatSelect()
      addRecentChat()
    } catch (error) {
      console.error('Error loading chat history:', error);
      toast.error('An error occurred while loading the chat history.');
    }
  };

  

  const handleModelSelect = async (selectedModel: ModelData) => {
    if (selectedModel) {
      setLoadingModel(true);

      try {
        const response = await axiosLLM.get('/api/backend/loadModel', {
          params: { modelId: selectedModel.modelId },
        });

        // Handle specific backend responses
        if (
          response.data === "There is already a loaded model, please unload the model first." ||
          response.data === "There is a loading model process happening now."
        ) {
          toast.warning(response.data);
        } else {
          setSelectedModel(selectedModel);
        }
      } catch (error) {
        console.error('Error loading model:', error);
        toast.error('An error occurred while loading the model.');
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

      // Check for loaded model
      const loadedModelResponse = await axiosLLM.get<string | null>('/api/backend/getLoadedModel');
      const loadedModelId = loadedModelResponse.data;

      if (loadedModelId != selectedModel?.modelId) {
        toast.warning("Another model is currently loaded into TAG. You are being redirected to the previous page.");
        setSelectedModel(null);
        setMessages([]);
      }

      let additionalContext = ""
      let promptMessages = [{"role": "system",  "content": `Please answer the question in the context of ${selectedModel?.project}`},
                            {"role": "user",    "content": `${formattedText}`}]

      // If current loaded model support RAG we should enrich the LLM with relevant context
      if (selectedModel?.isRagEnabled) {
        const queryRetrievalpayload = {
          text: formattedText,
          projectName: selectedModel?.project,
          modelName: selectedModel?.modelName,
          modelId: selectedModel?.modelId
        }

        const queryRetrievalResponse = await axiosBE.get('/api/rag/queryRetrieval', { params: queryRetrievalpayload });
        const relevantCodeSnippetts = queryRetrievalResponse.data.result

        const metadataRetrievalpayload = {
          relevantMetadata: relevantCodeSnippetts,
          projectName: selectedModel?.project,
        }

        const metadataRetrievalResponse = await axiosBE.post('/api/rag/metadataRetrieval', metadataRetrievalpayload)
        additionalContext = metadataRetrievalResponse.data.result
        promptMessages = [...promptMessages, {"role": "context", "content": `${additionalContext}`}]   
      }                         
      
      const inferencePayload = {
        messages: promptMessages,
        temperature: temperature.toString(),
        sessionId: sessionId
      }
      console.log("???")
      console.log(inferencePayload)
      const response = await fetch(`${AXIOS_LLM_IP}/api/backend/inference`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json', // Specify that you're sending JSON
        },
        body: JSON.stringify(inferencePayload),
      });
      console.log("!!")
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      if (!response.body) throw new Error('ReadableStream not supported!');
      
      // Monitor each model (based on unique uuid) by checking how many times users leverage the latest for inference 
      await axiosBE.post('/api/backend/addInferenceCounter', { modelId: selectedModel?.modelId, modelName: selectedModel?.modelName });

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
            const assistantTag = selectedModel?.promptTemplate?.assistant_tag || '';
            const endTag = selectedModel?.promptTemplate?.end_tag || '';

            let outputText = '';
            if (assistantTag && accumulatedText.includes(assistantTag)) {
              outputText = accumulatedText.split(assistantTag)[1];
            } else if (endTag && accumulatedText.includes(endTag)) {
              outputText = accumulatedText.split(endTag)[1];
            } else {
              outputText = accumulatedText;
            }

            lastMessage.text = outputText.trim();
          }
          updateCurrentChat(updatedMessages, sessionId, selectedModel?.modelId); // Update the chat in the DB
          console.log("did i get here?")
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
    // const startTag = selectedModel.promptTemplate?.user_tag || '';
    // const endTag = selectedModel.promptTemplate?.end_tag || '';
    // const assistantTag = selectedModel.promptTemplate?.assistant_tag || '';

    // Construct the message using the dynamic prompt template
    // const userMessageText = `${startTag}${text}${endTag} ${assistantTag}`;
    const userMessage: ChatMessage = {
      id: new Date().toISOString(),
      text: text,
      sender: 'user',
    };

    setMessages([...messages, userMessage]);
  
    setIsStreaming(true);
    sendQuestion(text);
  };

  const handleSaveClick = (userLatestMessage: string, promptLatestMessage: string) => {
    setPromptUserLatestMessage(userLatestMessage);
    setPromptLLMLatestMessage(promptLatestMessage);
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

    // Function to format a single message based on the sender
    const formatMessage = (message: ChatMessage): string => {
      return message.sender === 'user' ? `User: ${message.text}` : `LLM: ${message.text}`;
    };

    // Function to aggregate all messages
    const aggregateMessages = (messages: ChatMessage[]): string => {
      return messages.map(formatMessage).join('\n');
    };

    try {
      const payload = {
        modelId: selectedModel.modelId,
        modelName: selectedModel.modelName,
        trainingName: selectedModel.trainingName,
        promptEntireText: aggregateMessages(messages),
        promptUserLastQuestionText: promptUserLatestMessage,
        promptLLMLastAnswerText: promptLLMLatestMessage,
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
      await axiosLLM.get('/api/backend/stopInference', { params: { sessionId: sessionId } });
      setIsStreaming(false);
    } catch (error) {
      console.error('Error stopping inference:', error);
    }
  };

  const handleRatingClick = (idx: number) => {
    setCurrentRatingIdx(idx);
    setIsRatingModalOpen(true);
  };

  const handleRatingModalClose = () => {
    setIsRatingModalOpen(false);
    setCurrentRatingIdx(-1);
  };

  const handleRatingSave = async (rating: number, ratingText: string) => {
    if (currentRatingIdx === -1) return;

    setMessageRatings({ ...messageRatings, [currentRatingIdx]: { rating, ratingText } });
    setMessageIsRated({ ...messageIsRated, [currentRatingIdx]: true });

    // Send API request with prompt and rating details
    const userPrompt = messages[currentRatingIdx - 1].text;
    const botResponse = messages[currentRatingIdx].text;

    try {
      const payload = {
        modelId: selectedModel?.modelId,
        prompt: userPrompt,
        response: botResponse,
        rating,
        ratingText
      };
      await axiosBE.post('/api/backend/ratePrompt', payload);
      console.log('Rate saved successfully');
    } catch (error) {
      console.error('Error rating prompt:', error);
    }
  };


  const handleUnLoad = async () => {
    try {
      await axiosLLM.get('/api/backend/unloadModel');
    } catch (error) {
      console.error('Error stopping inference:', error);
    }
  };

  // Some browsers or environments (e.g., older browsers, certain versions of Safari, or if running in a non-HTTPS environment) may not
  // support the clipboard API or parts of it. The writeText method may be unavailable, leading to this error.
  // The Clipboard API (navigator.clipboard) requires the page to be served over HTTPS (except for localhost).
  // If you're running the app on a non-secure origin (e.g., http instead of https), the API won't be available.
  const copyToClipboard = (text: string) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        console.log('Text copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy text to clipboard', err);
      });
    } else {
      console.warn('Clipboard API not supported');
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

  const data = React.useMemo(() => (selectedModel ? [selectedModel] : []), [selectedModel]);
  
  const ReformatText = (text: string) => {
    const regularText = (line: string, type: RegExp, style: string) => {
      return line.replace(type, (_, text) => `<${style}>${text}</${style}>` ) + '\n';
    }

    const CODE = '```'
    const TITLE = /^### (.*)/
    const SUBTITLE = /^#### (.*)/
    const BOLD = /\*\*(.*?)\*\*/g

    const lines = text.split('\n'); 
    let [formattedText, insideCodeBlock, currentLanguage, codeBuffer] = ['', false, '', ''];
  
    for (const line of lines) {
      if (line.startsWith(CODE)) {
        if (insideCodeBlock) {
          // Closing code block after printing inside of it up until now
          const language = Prism.languages[currentLanguage] || Prism.languages.javascript;
          const highlightedCode = Prism.highlight(codeBuffer.trim(), language, currentLanguage);
          formattedText += `${highlightedCode}</code></pre>\n`;
          insideCodeBlock = false;
          codeBuffer = ''; 
        } else {
          // Opening code block after printing non-code lines up until now
          currentLanguage = line.slice(3).trim(); // Extract language (if any) after ```
          formattedText += `<pre class="language-${currentLanguage}"><code>`;
          insideCodeBlock = true;
        }
      } else if (insideCodeBlock) {
        // Append raw code directly inside the pre/code block
        codeBuffer += `${line}\n`;
      } else {
        // Handle non-code lines, we can add here any other ideas we have to make our responses nicer looking
        switch (true) {
          case TITLE.test(line):
            formattedText += regularText(line, TITLE, 'h2') 
            break;
          case SUBTITLE.test(line):
            formattedText += regularText(line, SUBTITLE, 'h3') 
            break;
          case BOLD.test(line):
            formattedText += regularText(line, BOLD, 'strong') 
            break;
          default:
            formattedText += line + '\n';
            break;
        }
      }
    }
  
    // If the text ends inside an unclosed code block, close it
    if (insideCodeBlock) {
      const language = Prism.languages[currentLanguage] || Prism.languages.javascript;
      const highlightedCode = Prism.highlight(codeBuffer.trim(), language, currentLanguage);
      formattedText += `${highlightedCode}</code></pre>\n`; 
    }
  
    return formattedText;
  };
  
  const isLlamaModel = () => {
    // currently only supporting text conventions of the llama models
    const finetunedSteps = selectedModel?.finetuneSteps;
    if (finetunedSteps && finetunedSteps.length > 0) {
      const baseModel = finetunedSteps[0]['base_model'];
      if (baseModel) {
        return baseModel.toLowerCase().includes('llama');
      }
    return false
    }
  }

  return (
    <>
      {loadingModel ? (
        <LoadingOverlay />
      ) : selectedModel ? (
        <div className="chat-container-wrapper">
          <ChatSidebar 
            drawerOpen={drawerOpen}
            setDrawerOpen={setDrawerOpen}
            data={data} 
            temperature={temperature} 
            setTemperature={setTemperature}
            isStreaming={isStreaming}
            clearChat={clearChat}
            unloadModel={unloadModel}
            handleChatSelect={handleChatSelect}
            currentChatId={currentChatId}
            historyChats={historyChats}
          />
          <MainContainer style={{marginLeft: drawerOpen ? '15%' : '0%', flexGrow: 1}}>
            <ChatContainer>
              <MessageList style={{padding: '10px'}}>
                {messages.map((message, idx) => (
                  <div key={message.id} style={{ position: 'relative', paddingBottom: '40px' }}>
                    <Message
                      model={{
                        message: isLlamaModel() ? ReformatText(message.text) : message.text, 
                        sentTime: 'just now',
                        sender: message.sender === 'user' ? 'You' : 'Bot',
                        direction: message.sender === 'user' ? 'outgoing' : 'incoming',
                        position: getPosition(idx, message.sender),
                      }}
                    />
                      {message.sender === 'bot' && (
                        <div style={{ position: 'absolute', bottom: '5px', left: '5px', display: 'flex', gap: '5px' }}>
                          <Tooltip title="Copy">
                            <IconButton onClick={() => copyToClipboard(message.text)} size="small" disabled>
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
                            <>
                              <Tooltip title="Regenerate">
                                <IconButton
                                  onClick={regenerateResponse}
                                  size="small"
                                >
                                  <AutorenewIcon />
                                </IconButton>
                              </Tooltip>

                              <Tooltip title="Rate">
                                <IconButton
                                  onClick={() => handleRatingClick(idx)}
                                  size="small"
                                  style={{ color: messageIsRated[idx] ? 'yellow' : '' }}
                                >
                                  <StarIcon />
                                </IconButton>
                              </Tooltip>
                            </>
                          )}
                          <Tooltip title="Save">
                            <IconButton onClick={() => handleSaveClick(messages[idx - 1].text, message.text)} size="small">
                              <SaveIcon />
                            </IconButton>
                          </Tooltip>
                        </div>
                      )
                    }
                  </div>
                ))}
              </MessageList>
              <MessageInput placeholder="Type your message here..." onSend={handleSend} disabled={loadingModel || isStreaming}
                attachButton={false}
                onPaste={(event) => {
                  event.preventDefault();
                  // Get plain text from clipboard
                  const text = event.clipboardData.getData('text/plain');
                  document.execCommand('insertText', false, text);
                }}
              />
            </ChatContainer>
          </MainContainer>
          <RatingModal
            open={isRatingModalOpen}
            onClose={handleRatingModalClose}
            onSave={handleRatingSave}
            initialRating={currentRatingIdx !== -1 ? messageRatings[currentRatingIdx]?.rating ?? 0 : 0}
            initialRatingText={currentRatingIdx !== -1 ? messageRatings[currentRatingIdx]?.ratingText ?? '' : ''}
          />
          <Dialog open={isModalOpen}
            onClose={handleModalClose}
            PaperProps={{
              style: { width: '50%', margin: '0 auto' }, // Custom width set to 50% and centered horizontally
            }}>
            <DialogTitle>Save Prompt</DialogTitle>
            <DialogContent>
              <TextField autoFocus margin="dense" label="Prompt Name" type="text" fullWidth variant="standard" value={promptName} onChange={handlePromptNameChange} />
            </DialogContent>
            <DialogActions>
              <Button onClick={handleModalClose} sx={{color: "black"}}>Cancel</Button>
              <Button onClick={handleSavePrompt} color="primary">Save</Button>
            </DialogActions>
          </Dialog>
        </div>
       ) : (
        <div className="model-selection-wrapper">
          <ModelSelection models={models} onSelectModel={handleModelSelect} />
        </div>
      )} <ToastContainer position="top-right" autoClose={5000} hideProgressBar />
    </>
  );
};

export default ChatComponent;