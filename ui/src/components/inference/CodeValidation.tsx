import React, { useState } from 'react';
import { Box, Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, CircularProgress, Typography } from '@mui/material';
import axiosBE from '../../http/axiosConfig'
import ValidationResponseViewer from './CodeValidationResponseViewer'

interface CodeValidationModalProps {
  open: boolean;
  onClose: () => void;
  llmResponse: string;
  repositoryLocation: string;
  modelType: 'llama' | 'qwen' | null;
  reformatText: (text: string, modelType: 'llama' | 'qwen') => string;
}

const CodeValidationModal: React.FC<CodeValidationModalProps> = ({
  open,
  onClose,
  llmResponse,
  repositoryLocation,
  modelType,
  reformatText
}) => {
  const [code, setCode] = useState<string>('');
  const [validationResponse, setValidationResponse] = useState<any>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);

  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const response = await axiosBE.post('/api/chat/evaluate', {
        code,
        repositoryLocation
      });
      
      // Ensure we're working with parsed JSON
      const jsonResponse = typeof response.data.result === 'string' 
        ? JSON.parse(response.data.result) 
        : response.data.result;
        
      setValidationResponse(jsonResponse);
    } catch (error) {
      console.error('Error validating code:', error);
      setValidationResponse({
        error: true,
        message: 'An error occurred during validation.'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleCodeChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCode(event.target.value);
  };

  const handleClose = () => {
    setCode('');
    setValidationResponse('');
    onClose();
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        style: { 
          minHeight: '80vh',
          padding: '20px'
        }
      }}
    >
      <DialogTitle>Code Validation</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
          <Box>
            <Typography 
              variant="h6" 
              sx={{ 
                fontSize: '1.125rem', 
                fontWeight: 600, 
                marginBottom: 1 
              }}
            >
              LLM Response:
            </Typography>
            <div 
              style={{ 
                backgroundColor: '#f9fafb',
                padding: '1rem',
                borderRadius: '0.375rem'
              }}
              dangerouslySetInnerHTML={{ 
                __html: modelType ? reformatText(llmResponse, modelType) : llmResponse 
              }} 
            />
          </Box>
          
          <TextField
            label="Paste the generated code for validation"
            multiline
            rows={8}
            value={code}
            onChange={handleCodeChange}
            variant="outlined"
            fullWidth
          />

          {validationResponse && (
            <Box sx={{ mt: 3 }}>
              <ValidationResponseViewer data={validationResponse} />
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} sx={{ color: "black" }}>
          Cancel
        </Button>
        <Button 
          onClick={handleValidate} 
          color="primary"
          disabled={!code || isValidating}
        >
          {isValidating ? <CircularProgress size={24} /> : 'Validate'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CodeValidationModal;