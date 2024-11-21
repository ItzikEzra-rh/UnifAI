import React from 'react';
import ChatComponent from './inference/ChatContainer'
import ProjectForm from './dataset/ProjectForm'
import FormTable from './shared/FormTable';
import Statistics from './statistics/Statistics'
import SavedPrompt from './inference/SavedPrompt'
import DataSetTable from './dataset/DataSetTable'
import TrainingForm from './training/TrainingForm'
import { Card, CardContent, Typography, Box, Button } from '@mui/material';
import '@fontsource/roboto/300.css';
import '../styles.css';

interface MainContentProps {
  content: string;
}

const MainContent: React.FC<MainContentProps> = ({ content }) => {

  const WelcomeContent = () => {
    return (
      <Card sx={{ maxWidth: '80%', margin: '50px auto', padding: 3, borderRadius: 2, boxShadow: 3 }}>
        <CardContent>
          <Typography variant="h2" component="h2">
            Welcome to GENIE!
          </Typography>
          <Typography variant="h5" gutterBottom>
            Welcome to GENIE (ראשי תיבות)! Here, we leverage artificial intelligence to create tailored tests efficiently and effectively. To help you better understand how it all works,
            here’s a brief overview of the core concepts and parameters involved in training AI models.
          </Typography>
          <Typography paragraph>
            Our <strong>primary objective</strong> is to establish a pre-tuned language model capable of producing high-quality Test Case code that adheres to the specific requirements of our automation team, including code styling and reusable conventions.
          </Typography>
          <Typography paragraph>
            Over the last few months, with advancements in AI capabilities and increased focus in Red Hat on AI/LLM, we have embarked on developing an in-house AI tool designed to generate test case (TC) code.
            
            We began by utilizing the NCS robot production test cases (TCs) and developing a parser to analyze the code of over 300 TCs. This parser will segment the code into a comprehensive logical dataset, which will subsequently be used to fine-tune our language model (LLM).
          </Typography>

          <Typography variant="h6" sx={{ color: 'red', fontWeight: 'bold', marginTop: 2 }}>
            Proof Of Concept Goal
            </Typography>
            <Typography paragraph>
            Our goal with the proof of concept (POC) is to enable users with basic knowledge of robot to request the generation of new test cases (TCs) from the language model (LLM) and receive high-quality results. The generated tests will adhere to the same conventions as the existing tests in the project.
          </Typography>

          <Box sx={{ margin: '20px 0', position: 'relative', overflow: 'hidden', paddingTop: '56.25%' /* 16:9 aspect ratio */ }}>
            <iframe
              src="https://docs.google.com/presentation/d/e/2PACX-1vSk0sFE-y0og_QYcTgLP4jjPl51H07UGQb170mFjvKb32A0FMBOUctGykFEFM8RZuNORQpxFv5FK4e-/embed?start=false&loop=false&delayms=3000"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                border: 'none',
              }}
              allowFullScreen
              title="TAG Presentation"
            ></iframe>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'center', marginTop: 3 }}>
            <Button variant="contained" color="primary">
              Learn More
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const InfoContent = () => {
    return (
      <Card sx={{ maxWidth: '80%', margin: '50px auto', padding: 3, borderRadius: 2, boxShadow: 3 }}>
        <CardContent>
          <Typography variant="h2" component="h2">
            Understanding AI and Model Training Parameters
          </Typography>

          <Typography variant="h5" gutterBottom>
            What is AI?
          </Typography>
          <Typography paragraph>
            Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed
            to think, learn, and make decisions.
            At its core, AI uses algorithms and data to identify patterns and provide outputs.
            In the context of test generation, AI models analyze a wide range of input data, learn from it,
            and produce customized questions, options, and solutions based on your requirements.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const getContentElement = (content: string) => {
    switch (content) {
      case 'Welcome Content': return <WelcomeContent />;
      case 'Info Content': return <InfoContent />;
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
