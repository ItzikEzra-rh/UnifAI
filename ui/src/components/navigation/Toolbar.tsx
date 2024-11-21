import React, { useState, useEffect } from 'react';
import { Breadcrumbs, Menu, MenuItem, Button, FormControl, InputLabel, Select, SelectChangeEvent } from '@mui/material';
import { DATA_SCIENCE_ROLE, USER_ROLE } from '../types/roles';
import RedHatLogoTAG from '../../assets/RedhatLogoNew.png';
import SendIcon from '@mui/icons-material/Send';
import HelpIcon from '@mui/icons-material/Help';
import { StyledBreadcrumb } from '../shared/StyledBreadcrumb';

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
  { title: 'About', items: [{ label: 'Welcome', content: 'Welcome Content' }, { label: 'More about AI', content: 'Info Content' }] },
  { title: 'Dataset', items: [{ label: 'Creating Dataset', content: 'Form Content' }, { label: 'Available Datasets', content: 'Dataset Table' }] },
  { title: 'Training', items: [{ label: 'Train New Model', content: 'Train Form' }, { label: 'Available Trained Models', content: 'Form Table' }] },
  { title: 'Inference', items: [{ label: 'Generate Automatic Test', content: 'Chatbot Prompt' }, { label: 'Saved Prompts', content: 'Saved Prompts' }] },
  { title: 'Statistics', items: [{ label: 'Graphs', content: 'Advanced Statistics' }] },
];

const dropdownUserItems: DropdownItems[] = [
  { title: 'About', items: [{ label: 'Welcome', content: 'Welcome Content' }, { label: 'More about AI', content: 'Info Content' }] },
  { title: 'Inference', items: [{ label: 'Generate Automatic Test', content: 'Chatbot Prompt' }, { label: 'Saved Prompts', content: 'Saved Prompts' }] },
  { title: 'Statistics', items: [{ label: 'Graphs', content: 'Advanced Statistics' }] },
];

const Toolbar: React.FC<ToolbarProps> = ({ role, setRole, setContent }) => {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [dropdownList, setDropdownList] = useState<DropdownItems[]>(dropdownUserItems);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuTitle, setMenuTitle] = useState<string>('');

  useEffect(() => {
    role === DATA_SCIENCE_ROLE ? setDropdownList(dropdownAllItems) : setDropdownList(dropdownUserItems);
  }, [role]);

  const handleBreadcrumbClick = (event: React.MouseEvent<HTMLElement>, title: string) => {
    setAnchorEl(event.currentTarget);
    setMenuTitle(title);
  };

  const handleMenuItemClick = (item: DropdownItem) => {
    setSelectedItem(item.label); // Update the selected item
    setContent(item.content);     // Update the content
    setAnchorEl(null);            // Close the dropdown by setting anchorEl to null
  };

  const handleMenuClose = () => {
    setAnchorEl(null); // Close the menu
  };

  const handleRoleChange = (event: SelectChangeEvent) => {
    setRole(event.target.value);
  };

  return (
    <div className="toolbar">
      <div className="logo">
        <img src={RedHatLogoTAG} alt="Logo" className="logo-image" />
      </div>

      <div className="breadcrumbs">
        <Breadcrumbs aria-label="breadcrumb">
          {dropdownList.map((dropdown) => (
            <StyledBreadcrumb
              key={dropdown.title}
              component="button"
              label={dropdown.title}
              onClick={(event) => handleBreadcrumbClick(event, dropdown.title)}
            />
          ))}
        </Breadcrumbs>
      </div>

      {/* Dropdown Menus */}
      {dropdownList.map((dropdown) => (
        <Menu
          key={dropdown.title}
          anchorEl={anchorEl}
          open={menuTitle === dropdown.title && Boolean(anchorEl)} // Only open if this menu is active
          onClose={handleMenuClose} // Close menu when clicking outside or when an item is selected
        >
          {dropdown.items.map((item) => (
            <MenuItem
              key={item.label}
              selected={selectedItem === item.label}
              onClick={() => handleMenuItemClick(item)} // Close the dropdown on item click
            >
              {item.label}
            </MenuItem>
          ))}
        </Menu>
      ))}

      <div className="toolbar-buttons">
        <FormControl variant="outlined" className="role-selection">
          <InputLabel>Role Selection</InputLabel>
          <Select value={role} onChange={handleRoleChange} label="Role Selection">
            <MenuItem value={USER_ROLE}>User Role</MenuItem>
            <MenuItem value={DATA_SCIENCE_ROLE}>Data Science Role</MenuItem>
          </Select>
        </FormControl>
        <Button variant="contained" endIcon={<SendIcon />}>Log In</Button>
        <Button variant="contained" endIcon={<HelpIcon />}>Support</Button>
      </div>
    </div>
  );
};

export default Toolbar;
