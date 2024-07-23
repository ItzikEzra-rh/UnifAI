import React from 'react';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { Box, Typography } from '@mui/material';

const SuccessMessage: React.FC = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'row',
        color: 'white',
        padding: '50px',
        borderRadius: '8px',
        textAlign: 'center',
        height: '20vh', // Full height to ensure it covers the entire screen
      }}
    >
      <CheckCircleIcon sx={{ fontSize: 100, color: 'white', fill: 'green !important'  }} />
      <Typography
        variant="h5"
        sx={{
          margin: '20px',
        }}
      >
        Form has been submitted, training will start soon
      </Typography>
    </Box>
  );
};

export default SuccessMessage;
