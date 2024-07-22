import React from 'react';
import '../styles.css';
import RedHatLogo from '../assets/RedhatLogo.png';
import { Button } from '@mui/material';

const TopToolbar: React.FC = () => {
  return (
    <div className="top-toolbar">
      <div className="logo">
        <img src={RedHatLogo} alt="Logo" className="logo-image" />
      </div>
      <div className="toolbar-buttons">
        <Button variant="outlined" className="custom-button">Log In</Button>
        <Button variant="outlined" className="custom-button">Support</Button>
      </div>
    </div>
  );
};

export default TopToolbar;
