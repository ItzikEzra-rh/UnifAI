import React, { useState } from 'react';
import TopToolbar from './components/TopToolbar';
import MainToolbar from './components/MainToolbar';
import MainContent from './components/MainContent';
import './styles.css';
import {DATA_SCIENCE_ROLE, USER_ROLE} from './components/types/roles'

const App: React.FC = () => {
  const [content, setContent] = useState('Select an option from the toolbar.');
  const [role, setRole] = useState<string>(USER_ROLE); // Default role

  return (
    <div className="app">
      <TopToolbar role={role} setRole={setRole} />
      <div className="main-section-container">
        <div className="main-section">
          <MainToolbar setContent={setContent} role={role} />
          <MainContent content={content} />
        </div>
      </div>
    </div>
  );
};

export default App;