import React from 'react';
import ChatComponent from './inference/ChatContainer'
import ProjectForm from './dataset/ProjectForm'
import FormTable from './shared/FormTable';
import Statistics from './statistics/Statistics'
import SavedPrompt from './inference/SavedPrompt'
import DataSetTable from './dataset/DataSetTable'
import TrainingForm from './training/TrainingForm'
import '../styles.css';
import WelcomeContent from './about/WelcomeContent';
import AIContent from './about/AIContent';

interface MainContentProps {
  content: string;
}

const MainContent: React.FC<MainContentProps> = ({ content }) => {
  const getContentElement = (content: string) => {
    switch (content) {
      case 'Welcome Content': return <WelcomeContent />;
      case 'AI Content': return <AIContent />;
      case 'Form Content': return <ProjectForm />;
      case 'Train Form': return <TrainingForm />;
      case 'Form Table': return <FormTable />;
      case 'Dataset Table': return <DataSetTable />
      case 'Chatbot Prompt': return <ChatComponent />;
      case 'Saved Prompts': return <SavedPrompt />;
      case 'Advanced Statistics': return <Statistics />;
      default: return content;
    }
  }

  return (
    <div className="main-content">
      {getContentElement(content)}
    </div>
  );
};

export default MainContent;
