import React, { useState } from 'react';
import TopToolbar from './components/TopToolbar';
import MainToolbar from './components/MainToolbar';
import MainContent from './components/MainContent';
import './styles.css';

const App: React.FC = () => {
  const [content, setContent] = useState('Select an option from the toolbar.');

  return (
    <div className="app">
      <TopToolbar />
      <div className="main-section-container">
        <div className="main-section">
          <MainToolbar setContent={setContent} />
          <MainContent content={content} />
        </div>
      </div>
    </div>
  );
};

export default App;