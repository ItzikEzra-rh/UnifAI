import React from 'react';
import '../styles.css';
import RedHatLogo from '../assets/RedhatLogo.png';
import RedHatLogoTAG from '../assets/RedhatLogoNew.png'
import { Button, FormControl, InputLabel, MenuItem, Select, SelectChangeEvent } from '@mui/material';
import {DATA_SCIENCE_ROLE, USER_ROLE} from './types/roles'

interface TopToolbarProps {
  role: string;
  setRole: (role: string) => void;
}

const TopToolbar: React.FC<TopToolbarProps> = ({ role, setRole }) => {
  const handleRoleChange = (event: SelectChangeEvent) => {
    setRole(event.target.value);
  };

  return (
    <div className="top-toolbar">
      <div className="logo">
        <img src={RedHatLogoTAG} alt="Logo" className="logo-image" />
      </div>
      <div className="toolbar-buttons">
        <FormControl variant="outlined" className="role-selection">
          <InputLabel>Role Selection</InputLabel>
          <Select value={role} onChange={handleRoleChange} label="Role Selection">
            <MenuItem value={USER_ROLE}> User Role </MenuItem>
            <MenuItem value={DATA_SCIENCE_ROLE}> Data Science Role </MenuItem>
          </Select>
        </FormControl>
        <Button variant="outlined" className="custom-button">Log In</Button>
        <Button variant="outlined" className="custom-button">Support</Button>
      </div>
    </div>
  );
};

export default TopToolbar;
