import React from 'react';
import Dropdown from './Dropdown';
import '../styles.css';
import ChatComponent from './ChatContainer';

interface MainToolbarProps {
  setContent: (content: string) => void;
}

const dropdownItems = [
  { title: 'About',items: [{ label: 'Welcome', content: 'Welcome Content' }]},
  { title: 'Form', items: [{ label: 'Fill Form', content: 'LLM Content' }]},
];


const MainToolbar: React.FC<MainToolbarProps> = ({ setContent }) => {
  return (
    <div className="main-toolbar">
      {dropdownItems.map((dropdown) => (
        <Dropdown key={dropdown.title} title={dropdown.title}>
          {dropdown.items.map((item) => (
            <div
              key={item.label}
              className="dropdown-item"
              onClick={() => setContent(item.content)}
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