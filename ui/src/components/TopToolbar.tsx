import React from 'react';
import '../styles.css';
import RedHatLogo from '../assets/RedhatLogo.png';

const TopToolbar: React.FC = () => {
  return (
    <div className="top-toolbar">
      <div className="logo">
        <img src={RedHatLogo} alt="Logo" className="logo-image" />
      </div>
    </div>
  );
};

export default TopToolbar;
