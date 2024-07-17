import React, { useState } from 'react';
import { MainContainer, ChatContainer, MessageList, Message, MessageInput } from '@chatscope/chat-ui-kit-react';
import '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import axios from 'axios';

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

const ChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const handleSend = async (text: string) => {
    const userMessage: ChatMessage = {
      id: new Date().toISOString(),
      text,
      sender: 'user',
    };

    setMessages([...messages, userMessage]);

    try {
      const response = await axios.post('/chat', { message: text });
      const botMessage: ChatMessage = {
        id: new Date().toISOString(),
        text: response.data.answer,
        sender: 'bot',
      };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Error communicating with chat API', error);
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

  return (
    <div style={{ height: '100%', border: '1px solid #ccc', padding: '10px' }}>
      <MainContainer>
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
          <MessageInput placeholder="Type your message here..." onSend={handleSend} />
        </ChatContainer>
      </MainContainer>
    </div>
  );
};

export default ChatComponent;
