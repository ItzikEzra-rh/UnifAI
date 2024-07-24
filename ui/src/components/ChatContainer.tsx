import React, { useEffect, useState } from 'react';
import { MainContainer, ChatContainer, MessageList, Message, MessageInput } from '@chatscope/chat-ui-kit-react';
import { useTable, useSortBy, Column } from 'react-table';
import {ModelData} from './types/constants'
import '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import axios from 'axios';
import '../styles.css';

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

const ChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [data, setData] = useState<ModelData[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const initalData : ModelData[] = [
        {modelName: 'NCS', modelMaxSeqLen: 1000},
      ]
      setData(initalData)
    };

    fetchData();
  }, []);

  const columns: Column<ModelData>[] = React.useMemo(
    () => [
      { Header: 'Model Name', accessor: 'modelName' },
      { Header: 'Model Max Seq Len', accessor: 'modelMaxSeqLen' },
    ],
    []
  );

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

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({ columns, data }, useSortBy);

  return (
    <div style={{ height: '100%', border: '1px solid #ccc', padding: '10px' }}>
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
          <MessageInput placeholder="Type your message here..." onSend={handleSend} />
        </ChatContainer>
      </MainContainer>
    </div>
  );
};

export default ChatComponent;
