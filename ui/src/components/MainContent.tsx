import React from 'react';
import ChatComponent from './inference/ChatContainer'
import ProjectForm from './dataset/ProjectForm'
import FormTable from './shared/FormTable';
import Statistics from './statistics/Statistics'
import SavedPrompt from './inference/SavedPrompt'
import DataSetTable from './dataset/DataSetTable'
import TrainingForm from './training/TrainingForm'
import { Card, CardContent, Typography } from '@mui/material';
import '../styles.css';

interface MainContentProps {
  content: string;
}

const MainContent: React.FC<MainContentProps> = ({ content }) => {

  const WelcomeContent = () => {
    return (
      <Card className='info'>
        <CardContent>
          <Typography variant="h2" component="h2" style={{ textAlign: 'center' }}>
            Welcome to GENIE!
          </Typography>
          <br></br>
          <Typography variant="h5" paragraph>
            Our <strong>primary objective</strong> is to establish a pre-tuned language model capable of producing high-quality Test Case code that adheres to the specific requirements of our automation team, including code styling and reusable conventions.
          </Typography>
          <Typography paragraph>
            Over the last few months, with advancements in AI capabilities and increased focus in Red Hat on AI/LLM, we have embarked on developing an in-house AI tool designed to generate test case (TC) code.
            <br></br>
            We began by utilizing the NCS robot production test cases (TCs) and developing a parser to analyze the code of over 300 TCs. This parser will segment the code into a comprehensive logical dataset, which will subsequently be used to fine-tune our language model (LLM).
          </Typography>
          <Typography variant="h5" style={{ textAlign: 'center' }}> Proof Of Concept Goal </Typography>
          <br></br>
          <Typography paragraph>
            Our goal with the proof of concept (POC) is to enable users with basic knowledge of robot to request the generation of new test cases (TCs)
            from the language model (LLM) and receive high quality results. The generated tests will adhere to the same conventions as the existing tests in the project.
          </Typography>
          <div style={{ margin: '50px auto', width: '80%' }}>
            <iframe
              src="https://docs.google.com/presentation/d/e/2PACX-1vSk0sFE-y0og_QYcTgLP4jjPl51H07UGQb170mFjvKb32A0FMBOUctGykFEFM8RZuNORQpxFv5FK4e-/embed?start=false&loop=false&delayms=3000"
              frameBorder="0"
              width="100%"
              height="480"
              allowFullScreen
              title="TAG Presentation"
            ></iframe>
          </div>

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
