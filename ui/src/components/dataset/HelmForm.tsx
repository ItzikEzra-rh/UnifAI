import React, { useState } from 'react';
import { Button, Box } from '@mui/material';
import SuccessMessage from '../shared/SuccessMessage';
import { SubmitHandler } from 'react-hook-form';
import axios from '../../http/axiosConfig';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import UploadHelmJson from './UploadHelmJson';
import CreateHelmJson from '../inference/CreateHelmJson';
import { useNavigate } from 'react-router-dom';  // Import the useNavigate hook

const HelmForm: React.FC = () => {
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [mode, setMode] = useState<'create' | 'upload'>('upload');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate(); // Create navigate instance

  const onSubmit: SubmitHandler<any> = async (data, event) => {
    event?.preventDefault(); 
    try {
      setIsLoading(true);
      console.log('Submitting JSON file data:', data);
      const res = await axios.post('/api/dpr/install', { data: data, mode: mode });
      if (res.status === 200) {
        setFormSubmitted(true);
        console.log('Form submitted successfully:', data);
        // Redirect to /deployed-datasets after successful submission
        setTimeout(() => {
          navigate('/deployed-datasets'); // Trigger navigation
        }, 2000); // Delay to allow user to see success message
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      toast.warn('An error occurred while submitting.');
    } finally {
      setIsLoading(false);
    }
  };

  const FormComponent = mode === 'upload' ? UploadHelmJson : CreateHelmJson;

  return (
    <>
      <Box className="mode-selection">
        <Button onClick={() => setMode('upload')} variant={mode === 'upload' ? 'contained' : 'outlined'}>
          Upload JSON File
        </Button>
        <Button onClick={() => setMode('create')} variant={mode === 'create' ? 'contained' : 'outlined'}>
          Create JSON File
        </Button>
      </Box>

      {!formSubmitted ? <FormComponent onSubmit={onSubmit} isLoading={isLoading} /> : <SuccessMessage />}

      <ToastContainer position="top-right" autoClose={5000} hideProgressBar />
    </>
  );
};

export default HelmForm;
