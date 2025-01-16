import React from 'react';
import { Paper, Typography, List, ListItem, ListItemButton, ListItemText, ListItemIcon, Divider, Box} from '@mui/material';
import MessageIcon from '@mui/icons-material/Message';
import HistoryIcon from '@mui/icons-material/History';

interface ChatMessage {
    id: string;
    text: string;
    sender: 'user' | 'bot';
  }

interface ChatHistoryProps {
  isStreaming: boolean;
  onChatSelect: (chatId: string, messages: ChatMessage[]) => void;
  currentChatId: string;
  historyChats: HistoryChat[];
}

export interface HistoryChat {
  id: string;
  name: string;
  timestamp: string;
  messages: ChatMessage[];
  firstMessage: string;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ isStreaming, onChatSelect, currentChatId, historyChats }) => {
  console.log(isStreaming)
  console.log(historyChats)
  return (
    <Paper elevation={3} sx={{ width: '95%', marginTop: '10px',display: 'flex', flexDirection: 'column',}}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HistoryIcon /> Chat History
        </Typography>
      </Box>

      <List sx={{ overflow: 'auto', flexGrow: 1 }}>
        {historyChats.map((chat, index) => (
          <React.Fragment key={chat.id}>
            <ListItem disablePadding>
              <ListItemButton
                selected={currentChatId === chat.id}
                disabled={isStreaming}
                onClick={() => onChatSelect(chat.id, chat.messages)}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(25, 118, 210, 0.08)',
                  },
                }}
              >
                <ListItemIcon>
                  <MessageIcon />
                </ListItemIcon>
                <ListItemText
                  primary={chat.name}
                  secondary={
                    <React.Fragment>
                      <Typography component="span" variant="body2" color="text.primary" sx={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                        {chat.firstMessage}
                      </Typography>
                      <Typography component="span" variant="caption" color="text.secondary">
                        {chat.timestamp}
                      </Typography>
                    </React.Fragment>
                  }
                />
              </ListItemButton>
            </ListItem>
            {index < historyChats.length - 1 && <Divider />}
          </React.Fragment>
        ))}
        {historyChats.length === 0 && (
          <ListItem>
            <ListItemText 
              primary="No chat history yet"
              sx={{ textAlign: 'center', color: 'text.secondary' }}
            />
          </ListItem>
        )}
      </List>
    </Paper>
  );
};

export default ChatHistory;