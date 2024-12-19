import { Box, Card, CardContent, Typography } from '@mui/material';
import RedHatAI from '../../assets/RedHatAI.png';

const AiContent = () => {
    return (
        <Card className='info'>
            <CardContent sx={{marginLeft: 5, marginRight: 5}}>
                <Typography variant="h4" component="h4">
                    <b>Understanding AI and Model Training Parameters</b>
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
                            • Sequence length defines the maximum number of tokens (words, phrases, or symbols) that the AI can process at once.
                            <br></br>
                            • Longer sequences capture more context but may increase computational requirements.
                        </div>
                    2. <b>Model Size</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • This refers to the number of parameters in an AI model, which influences its capability to learn and generalize from data. Larger models tend to be more powerful but require more training resources.
                        </div>
                    3. <b>Learning Rate</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • The learning rate determines how quickly the model adapts to new data during training. It’s a balance—too high, and the model may overshoot optimal solutions; too low, and training may take unnecessarily long.
                        </div>
                    4. <b>Epochs</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • An epoch is one complete pass through the entire training dataset. More epochs allow the model to refine its learning but can lead to overfitting if overdone.
                        </div>
                    5. <b>Batch Size</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • Batch size indicates how many samples the model processes before updating its parameters. It impacts training speed and memory usage.
                        </div>
                    6. <b>Validation Split</b>
                        <br></br>
                        <div style={{marginLeft: 30}}>
                            • This parameter defines the proportion of data used to evaluate the model’s performance during training, ensuring it generalizes well to unseen data.
                        </div>
                    <br></br>
                </Typography>
                <Typography variant="h5" component="h5">
                    <b>How AI Creates Tests</b>
                </Typography>
                <br></br>
                <Typography variant="body1" sx={{fontSize: '18px'}}>
                    <div style={{marginLeft: 30}}>
                        1. <b>Data Processing: </b> The AI analyzes input data, including text, patterns, and user requirements. <br></br>
                        2. <b>Training the Model: </b>Using the parameters mentioned above, the AI fine-tunes its understanding of the data to generate accurate, contextually appropriate questions.<br></br>
                        3. <b>Test Generation: </b> The trained model creates questions, answers, and explanations that meet your specified needs.
                    </div>
                </Typography>
                <br></br>
                <Typography variant="body1" sx={{fontSize: '18px'}}>
                    Our system is designed to make these technical aspects seamless, allowing you to focus on utilizing high-quality tests tailored to your goals.
                    <br></br>
                    For more detailed insights or custom configurations, feel free to explore our documentation or contact our support team.
                </Typography>
            </CardContent>
        </Card>
    );
  }

  export default AiContent;
