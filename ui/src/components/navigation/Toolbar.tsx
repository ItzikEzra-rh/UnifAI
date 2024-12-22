import React, { useState, useEffect, useRef } from 'react';
import { Menu, MenuItem, Button, FormControl, Select, SelectChangeEvent, ButtonGroup, InputLabel } from '@mui/material';
import { DATA_SCIENCE_ROLE, USER_ROLE } from '../types/roles';
import RedHatLogoTAG from '../../assets/RedhatLogoNew.png';
import SendIcon from '@mui/icons-material/Send';
import HelpIcon from '@mui/icons-material/Help';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';

interface ToolbarProps {
  role: string;
  setRole: (role: string) => void;
  setContent: (content: string) => void;
}

interface DropdownItem {
  label: string;
  content: string;
}

interface DropdownItems {
  title: string;
  items: DropdownItem[];
}

const dropdownAllItems: DropdownItems[] = [
  { title: 'About', items: [{ label: 'Welcome', content: 'Welcome Content' }, { label: 'Understanding AI', content: 'Ai Content' }] },
  { title: 'Dataset', items: [{ label: 'Creating Dataset', content: 'Form Content' }, { label: 'Available Datasets', content: 'Dataset Table' }] },
  { title: 'Training', items: [{ label: 'Train New Model', content: 'Train Form' }, { label: 'Available Trained Models', content: 'Form Table' }] },
  { title: 'Inference', items: [{ label: 'Generate Automatic Test', content: 'Chatbot Prompt' }, { label: 'Saved Prompts', content: 'Saved Prompts' }] },
  { title: 'Statistics', items: [{ label: 'Graphs', content: 'Advanced Statistics' }] },
];

const dropdownUserItems: DropdownItems[] = [
  { title: 'About', items: [{ label: 'Welcome', content: 'Welcome Content'}, { label: 'Understanding AI', content: 'Ai Content' }] },
  { title: 'Inference', items: [{ label: 'Generate Automatic Test', content: 'Chatbot Prompt' }, { label: 'Saved Prompts', content: 'Saved Prompts' }] },
  { title: 'Statistics', items: [{ label: 'Graphs', content: 'Advanced Statistics' }] },
];

const Toolbar: React.FC<ToolbarProps> = ({ role, setRole, setContent }) => {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [dropdownList, setDropdownList] = useState<DropdownItems[]>(dropdownUserItems);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuTitle, setMenuTitle] = useState<string>('');
  const [selectedButton, setSelectedButton] = useState<string | null>(null); // Track the selected button
  const toolbarRef = useRef<HTMLDivElement>(null); // Ref for toolbar container

  useEffect(() => {
    role === DATA_SCIENCE_ROLE ? setDropdownList(dropdownAllItems) : setDropdownList(dropdownUserItems);
  }, [role]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (toolbarRef.current && !toolbarRef.current.contains(event.target as Node)) {
        setSelectedButton(null);
        setAnchorEl(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleClick = (event: React.MouseEvent<HTMLElement>, title: string) => {
    setAnchorEl(event.currentTarget);
    setMenuTitle(title);
    setSelectedButton(title);
  };

  const handleMenuItemClick = (item: DropdownItem) => {
    setSelectedItem(item.label);
    setContent(item.content);
    setAnchorEl(null);
    setSelectedButton(null);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleRoleChange = (event: SelectChangeEvent) => {
    setRole(event.target.value);
  };

  return (
    <div className="toolbar" ref={toolbarRef}>
      <div className="left-section">
        <a href="/">
          <img src={RedHatLogoTAG} alt="Logo" className="logo-image" />
        </a>
        <ButtonGroup variant="contained" className="dropdown-buttons" aria-label="Basic button group">
          {dropdownList.map((dropdown) => (
            <Button
              key={dropdown.title}
              endIcon={<KeyboardArrowDownIcon />}
              onClick={(event) => handleClick(event, dropdown.title)}
              className={selectedButton === dropdown.title ? 'selected' : ''}
            >
              {dropdown.title}
            </Button>
          ))}
        </ButtonGroup>
      </div>
      {dropdownList.map((dropdown) => (
        <Menu
          key={dropdown.title}
          anchorEl={anchorEl}
          open={menuTitle === dropdown.title && Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          {dropdown.items.map((item) => (
            <MenuItem
              key={item.label}
              selected={selectedItem === item.label}
              onClick={() => handleMenuItemClick(item)}
            >
              {item.label}
            </MenuItem>
          ))}
        </Menu>
      ))}

      <div className="toolbar-buttons">
        <FormControl variant="outlined" className="role-selection">
          <InputLabel>Role Selection</InputLabel>
          <Select value={role} onChange={handleRoleChange}>
            <MenuItem value={USER_ROLE}>User Role</MenuItem>
            <MenuItem value={DATA_SCIENCE_ROLE}>Data Science Role</MenuItem>
          </Select>
        </FormControl>
        <Button variant="contained" className="end-button" endIcon={<SendIcon />}>Log In</Button>
        <Button variant="contained" className="end-button" endIcon={<HelpIcon />}>Support</Button>
      </div>
    </div>
  );
};

export default Toolbar;
