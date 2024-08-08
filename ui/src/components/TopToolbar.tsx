import React from 'react';
import '../styles.css';
import RedHatLogo from '../assets/RedhatLogo.png';
import RedHatLogoTAG from '../assets/RedhatLogoNew.png'
import { Button } from '@mui/material';

const TopToolbar: React.FC = () => {
  return (
    <div className="top-toolbar">
      <div className="logo">
        <img src={RedHatLogoTAG} alt="Logo" className="logo-image" />
        {/* <span className="logo-text">TAG (Test Automation Generator)</span> */}
      </div>
      <div className="toolbar-buttons">
        <Button variant="outlined" className="custom-button">Log In</Button>
        <Button variant="outlined" className="custom-button">Support</Button>
      </div>
    </div>
  );
};

export default TopToolbar;
