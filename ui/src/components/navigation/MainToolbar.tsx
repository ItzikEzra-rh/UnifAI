import React, { useState, useEffect } from 'react';
import Dropdown from '../shared/Dropdown';
import '../../styles.css';
import ChatComponent from '../inference/ChatContainer';
import {DATA_SCIENCE_ROLE} from '../types/roles'

interface MainToolbarProps {
  setContent: (content: string) => void;
  role: string;
}

interface dropdownItem {
  label: string;
  content: string;
}

interface dropdownItems {
  title: string;
  items: dropdownItem[];
}

const dropdownAllItems: dropdownItems[] = [
  { title: 'About',items: [{ label: 'Welcome', content: 'Welcome Content' }]},
  { title: 'Dataset', items: [{ label: 'Creating Dataset', content: 'Form Content' }, { label: 'Available Datasets', content: 'Dataset Table' }]},
  { title: 'Training', items: [{ label: 'Train New Model', content: 'Train Form' }, { label: 'Avaliable Trained Models', content: 'Form Table' }]},
  { title: 'Inference', items: [{ label: 'Generate Automatic Test', content: 'Chatbot Prompt' }, { label: 'Saved Prompts', content: 'Saved Prompts' }]},
  { title: 'Statistics', items: [{ label: 'Graphs', content: 'Advanced Statistics' }]},
];

const dropdownUserlItems: dropdownItems[] = [
  { title: 'About',items: [{ label: 'Welcome', content: 'Welcome Content' }]},
  { title: 'Inference', items: [{ label: 'Generate Automatic Test', content: 'Chatbot Prompt' }, { label: 'Saved Prompts', content: 'Saved Prompts' }]},
  { title: 'Statistics', items: [{ label: 'Graphs', content: 'Advanced Statistics' }]},
]

const MainToolbar: React.FC<MainToolbarProps> = ({ setContent, role }) => {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [dropdownList, setDropdownList] = useState<dropdownItems[]>(dropdownUserlItems);

  useEffect(() => {
    role == DATA_SCIENCE_ROLE ? setDropdownList(dropdownAllItems) : setDropdownList(dropdownUserlItems);
  }, [role]);

  const handleItemClick = (item: any) => {
    setSelectedItem(item.label);
    setContent(item.content);
  };

  return (
    <div className="main-toolbar">
      {dropdownList.map((dropdown) => (
        <Dropdown key={dropdown.title} title={dropdown.title}>
          {dropdown.items.map((item) => (
            <div
              key={item.label}
              className={`dropdown-item ${selectedItem === item.label ? 'selected' : ''}`}
              onClick={() => handleItemClick(item)}
            >
              {item.label}
            </div>
          ))}
        </Dropdown>
      ))}
    </div>
  );
};

export default MainToolbar;