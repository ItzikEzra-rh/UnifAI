import React, { useState } from 'react';
import '../styles.css';

interface DropdownProps {
  title: string;
  children: React.ReactNode;
}

const Dropdown: React.FC<DropdownProps> = ({ title, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="dropdown">
      <div className="dropdown-title" onClick={() => setIsOpen(!isOpen)}>
        <span className={`arrow ${isOpen ? 'open' : ''}`}></span> {title}
      </div>
      {isOpen && (
        <div className="dropdown-content">
          {children}
        </div>
      )}
    </div>
  );
};

export default Dropdown;
