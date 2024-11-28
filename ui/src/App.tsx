import React, { useState } from 'react';
import MainContent from './components/MainContent';
import './styles.css';
import { USER_ROLE } from './components/types/roles';
import Toolbar from './components/navigation/Toolbar';

const App: React.FC = () => {
  const [content, setContent] = useState<string>('Welcome Content');
  const [role, setRole] = useState<string>(USER_ROLE);

  return (
    <div className="app">
      <div className="top-main-container">
        <Toolbar role={role} setRole={setRole} setContent={setContent} />
        <MainContent content={content} />
      </div>
    </div>
  );
};

export default App;
