import React from 'react';
import '../styles.css';
import ChatComponent from './ChatContainer'
import AIPicture from '../assets/AIPicture.png';
import ProjectForm from './ProjectForm'
import FormTable from './FormTable';

interface MainContentProps {
  content: string;
}

const MainContent: React.FC<MainContentProps> = ({ content }) => {

    const WelcomeContent = () => {
      return (
        <div>
          <p>
            Our <strong>primary objective</strong> is to establish a pre-tuned language model capable of producing high-quality Test Case code that
            adheres to the specific requirements of our automation team, including code styling and reusable conventions.
          </p>
          <p>
            Over the last few months, with advancements in AI capabilities and increased focus in Red Hat on AI/LLM,
            we have embarked on developing an in-house AI tool designed to generate test case (TC) code.
          </p>
          <p>
            We began by utilizing the NCS robot production test cases (TCs) and developing a parser to analyze the code of over 300 TCs.
            This parser will segment the code into a comprehensive logical dataset, which will subsequently be used to fine-tune our language model (LLM).
          </p> 
            <h2 style={{ color: 'red', fontWeight: 'bold', fontSize: 'small' }}> Proof Of Concept Goal </h2>
          <p>
            Our goal with the proof of concept (POC) is to enable users with basic knowledge of robot to request the generation of new test cases (TCs)
            from the language model (LLM) and receive high quality results. The generated tests will adhere to the same conventions as the existing tests in the project.
          </p>
          <img src={AIPicture} alt="AILogo" className="bottom-right-image" />
        </div>
      );
    } 

    const getContentElement = (content: string) =>  {
        switch(content) {
            case 'Welcome Content': return <WelcomeContent/>;
            case 'Form Content': return <ProjectForm/>;
            case 'Form Table': return <FormTable/>;
            case 'Chatbot Prompt': return <ChatComponent/>;
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
