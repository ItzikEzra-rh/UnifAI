import React from 'react';
import ChatComponent from './inference/ChatContainer'
import ProjectForm from './dataset/ProjectForm'
import FormTable from './shared/FormTable';
import Statistics from './statistics/Statistics'
import SavedPrompt from './inference/SavedPrompt'
import DataSetTable from './dataset/DataSetTable'
import TrainingForm from './training/TrainingForm'
import { Card, CardContent, Typography, Box, Button } from '@mui/material';
import '../styles.css';

interface MainContentProps {
  content: string;
}

const MainContent: React.FC<MainContentProps> = ({ content }) => {

  const WelcomeContent = () => {
    return (
      <Card sx={{ maxWidth: '80%', margin: '50px auto', padding: 3, borderRadius: 2, boxShadow: 3 }}>
        <CardContent>
          <Typography variant="h2" component="h2" style={{textAlign: 'center'}}>
            Welcome to GENIE!
          </Typography>

          <Typography variant="h5" paragraph>
            Our <strong>primary objective</strong> is to establish a pre-tuned language model capable of producing high-quality Test Case code that adheres to the specific requirements of our automation team, including code styling and reusable conventions.
          </Typography>
          <Typography paragraph>
            Over the last few months, with advancements in AI capabilities and increased focus in Red Hat on AI/LLM, we have embarked on developing an in-house AI tool designed to generate test case (TC) code.
            
            We began by utilizing the NCS robot production test cases (TCs) and developing a parser to analyze the code of over 300 TCs. This parser will segment the code into a comprehensive logical dataset, which will subsequently be used to fine-tune our language model (LLM).
          </Typography>

        
        </CardContent>
      </Card>
    );
  }

  const getContentElement = (content: string) => {
    switch (content) {
      case 'Welcome Content': return <WelcomeContent />;
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
