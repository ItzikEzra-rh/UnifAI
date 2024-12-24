import { Box, Card, CardContent, Typography } from '@mui/material';
import RedHatAI from '../../assets/RedHatAI.png';
import GenieLogoOrigin from '../../assets/GenieLogoOrigin.png';

const AiContent = () => {
    return (
        <Card className='info'>
            <CardContent sx={{marginLeft: 8, marginRight: 8}}>
                <Typography variant="h2" component="h2" style={{ textAlign: 'center', marginTop: '10px' }}>
                    Understanding AI and Model Training Parameters
                </Typography>
                <br></br>
                <Typography variant="body1" sx={{fontSize: '18px'}}>
                    Here on GENIE, we leverage artificial intelligence to create tailored tests efficiently and effectively. To help you better understand how it all works, here’s a brief overview of the core concepts and parameters involved in training AI models.
                </Typography>
                <br></br>
                
                <Box display="flex" alignItems="center">
                    <Typography variant="body1" sx={{ width: '60%', marginRight: 2, fontSize: 18 }}>
                    <Typography variant="h5" component="h5">
                        <b>What is AI?</b>
                    </Typography>
                    <br></br>
                        Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think, learn, and make decisions. At its core, AI uses algorithms and data to identify patterns and provide outputs.
                        <br></br>
                        In the context of test generation, AI models analyze a wide range of input data, learn from it, and produce customized questions, options, and solutions based on your requirements.
                    </Typography>
                    <div style={{display: 'flex', justifyContent: 'flex-end'}}>
                        <img
                        src={RedHatAI}
                        alt="Red Hat AI"
                        style={{ width: '50%', height: 'auto' }}
                        />
                    </div>
                </Box>
                <br></br>
                <Typography variant="h5" component="h5">
                    <b>Key Parameters in AI Training</b>
                </Typography>
                <br></br>
                <Typography variant="body1" sx={{fontSize: '18px'}}>
                    1. <b>Sequence Length</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Defines the maximum number of tokens (words, phrases, or symbols) that the AI can process at once.
                            <br></br>
                            • Longer sequences capture more context but may increase computational requirements.
                            <br></br>
                            • Model Max Sequence Length represents the absolute upper limit the model can handle.
                        </div>
                    2. <b>Model Size</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Refers to the number of parameters in an AI model, which influences its capability to learn and generalize from data.
                            <br></br>
                            • Larger models tend to be more powerful but require more training resources.
                        </div>
                    3. <b>Learning Rate</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Determines how quickly the model adapts to new data during training. 
                            <br></br>
                            • Balancing this is critical—too high, and the model may overshoot optimal solutions; too low, and training may take unnecessarily long.
                        </div>
                    4. <b>Epochs</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Represents one complete pass through the entire training dataset. 
                            <br></br>
                            • A larger epoch number allows the model to refine its learning but can lead to overfitting if overdone.
                        </div>
                    5. <b>Batch Size</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Indicates how many samples the model processes before updating its parameters. 
                            <br></br>
                            • Impacts training speed and memory usage.
                        </div>
                    6. <b>Validation Split</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Defines the proportion of data used to evaluate the model’s performance during training, ensuring it generalizes well to unseen data.
                        </div>
                    7. <b>Temperature</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Controls the randomness of the AI's output.
                            <br></br>
                            • A higher temperature produces more diverse and creative responses, while a lower value makes responses more deterministic.
                        </div>
                    8. <b>Save Steps</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Determines how often the model saves its progress during training.
                            <br></br>
                            • Frequent saves ensure minimal data loss in case of interruptions.
                        </div>
                    9. <b>Warmup Steps</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • A specified number of steps at the beginning of training where the learning rate gradually increases.
                            <br></br>
                            • Helps stabilize the model's learning process.
                        </div>
                    <br></br>
                </Typography>
                <Typography variant="h5" component="h5">
                    <b>How AI Creates Tests</b>
                </Typography>
                <br></br>
                <Typography variant="body1" sx={{fontSize: '18px'}}>
                    <div style={{marginLeft: 30}}>
                        1. <b>Data Processing: </b>  
                        <div style={{marginLeft: 30}}>
                            The AI analyzes input data, including text, patterns, and user requirements.
                        </div>
                        2. <b>Training the Model: </b>  
                        <div style={{marginLeft: 30}}>
                            Using the parameters mentioned above, the AI fine-tunes its understanding of the data to generate accurate, contextually appropriate questions.
                        </div>
                        3. <b>Test Generation: </b>  
                        <div style={{marginLeft: 30}}>
                            The trained model creates questions, answers, and explanations that meet your specified needs.
                        </div>
                    </div>
                </Typography>
                <br></br><br></br>
                <Box display="flex" alignItems="center">
                    <Typography variant="body1" sx={{ width: '60%', marginRight: 2, fontSize: 18 }}>
                    <Typography variant="h5" component="h5">
                        <b>Why choose GENIE?</b>
                    </Typography>
                        Our system is designed to make these technical aspects seamless, allowing you to focus on utilizing high-quality tests tailored to your goals.
                        <br></br>
                        For more detailed insights or custom configurations, feel free to contact our support team.
                    </Typography>
                    <div style={{display: 'flex', justifyContent: 'flex-end'}}>
                        <img
                        src={GenieLogoOrigin}
                        alt="Genie Logo Origin"
                        style={{ width: '30%', height: 'auto' }}
                        />
                    </div>
                </Box>
            </CardContent>
        </Card>
    );
  }

  export default AiContent;
