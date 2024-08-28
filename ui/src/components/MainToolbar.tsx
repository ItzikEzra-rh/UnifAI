import React, { useState } from 'react';
import Dropdown from './Dropdown';
import '../styles.css';
import ChatComponent from './ChatContainer';

interface MainToolbarProps {
  setContent: (content: string) => void;
}

const dropdownItems = [
  { title: 'About',items: [{ label: 'Welcome', content: 'Welcome Content' }]},
  { title: 'Training', items: [{ label: 'Train New Model', content: 'Form Content' }, { label: 'Avaliable Trained Models', content: 'Form Table' }]},
  { title: 'Inference', items: [{ label: 'Generate Automatic Test', content: 'Chatbot Prompt' }, { label: 'Saved Prompts', content: 'Saved Prompts' }]},
  { title: 'Statistics', items: [{ label: 'Graphs', content: 'Advanced Statistics' }]},
];


const MainToolbar: React.FC<MainToolbarProps> = ({ setContent }) => {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);

  const handleItemClick = (item: any) => {
    setSelectedItem(item.label);
    setContent(item.content);
  };

  return (
    <div className="main-toolbar">
      {dropdownItems.map((dropdown) => (
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