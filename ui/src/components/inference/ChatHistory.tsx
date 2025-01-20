import React, { useState } from 'react';
import axiosBE from '../../http/axiosConfig';
import { Paper, Typography, List, ListItem, ListItemButton, ListItemText, ListItemIcon, Divider, Box, ListItemSecondaryAction, IconButton, Dialog, DialogActions, DialogContent, DialogTitle, Button } from '@mui/material';
import MessageIcon from '@mui/icons-material/Message';
import HistoryIcon from '@mui/icons-material/History';
import DeleteIcon from '@mui/icons-material/Delete';
import moment from 'moment';

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
  setHistoryChats: (historyChats: HistoryChat[]) => void;
}

export interface HistoryChat {
  sessionId: string;
  timestamp: string;
  messages: ChatMessage[];
  firstMessage: string;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ isStreaming, onChatSelect, currentChatId, historyChats, setHistoryChats }) => {
  const [openModal, setOpenModal] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedFirstMessage, setSelectedFirstMessage] = useState<string | null>(null);

  const deleteSession = async (sessionId: string) => {
    try {
      const response = await axiosBE.post('/api/backend/deleteChatSession', {sessionId: selectedSessionId});
      console.log('Session deleted:', response.data);
      
      // Optionally, remove the deleted session from the state
      setHistoryChats(historyChats.filter((chat) => chat.sessionId !== sessionId));
      setOpenModal(false); // Close the modal after successful deletion
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleDeleteClick = (sessionId: string, firstMessage: string) => {
    setSelectedSessionId(sessionId);
    setSelectedFirstMessage(firstMessage);
    setOpenModal(true); // Open the confirmation modal
  };

  const handleCloseModal = () => {
    setOpenModal(false);
    setSelectedSessionId(null); // Clear the selected session ID
    setSelectedFirstMessage(null); // Clear the selected first message
  };

  const sortedChats = historyChats.sort((a, b) => {
    const dateA: Date = moment(a.timestamp, 'MMM DD, YYYY, hh:mm:ss A').toDate();
    const dateB: Date = moment(b.timestamp, 'MMM DD, YYYY, hh:mm:ss A').toDate();
    return dateB.getTime() - dateA.getTime(); // Compare using timestamps
  });

  return (
    <Paper elevation={3} sx={{ width: '95%', marginTop: '10px', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HistoryIcon /> Chat History
        </Typography>
      </Box>

      <List sx={{ overflow: 'auto', flexGrow: 1 }}>
        {sortedChats.map((chat, index) => (
          <React.Fragment key={index}>
            <ListItem disablePadding>
              <ListItemButton
                selected={currentChatId === chat.sessionId}
                disabled={isStreaming}
                onClick={() => onChatSelect(chat.sessionId, chat.messages)}
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
                  primary={chat.firstMessage}
                  secondary={
                    <React.Fragment>
                      <Typography component="span" variant="caption" color="text.secondary">
                        {chat.timestamp}
                      </Typography>
                    </React.Fragment>
                  }
                />
              </ListItemButton>
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleDeleteClick(chat.sessionId, chat.firstMessage)}
                >
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
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

      {/* Confirmation Modal */}
      <Dialog open={openModal} onClose={handleCloseModal}>
        <DialogTitle>Are you sure you want to delete this chat?</DialogTitle>
        <DialogContent>
          <Typography> You selected the chat starting with "{selectedFirstMessage}"</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseModal} sx={{color: 'black'}}>
            Cancel
          </Button>
          <Button
            onClick={() => {
              if (selectedSessionId) {
                deleteSession(selectedSessionId);
              }
            }}
            color="primary"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default ChatHistory;
