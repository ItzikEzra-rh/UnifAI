import { Card, CardContent, Typography } from '@mui/material';
import AiAgentGraph from '../../AiAgentsGraph.png';

const WelcomeContent = () => {
    return (
        <Card className='info'>
            <CardContent>
                <Typography variant="h2" component="h2" style={{ textAlign: 'center' }}>
                    Welcome to GENIE!
                </Typography>
                <br></br>
                <div style={{marginLeft: 30, marginRight: 30}}>
                    <Typography variant="h6">
                        <b>GENIE (Generative Engine for New Insights and Execution)</b> is an advanced AI-powered platform designed to revolutionize software development and quality assurance. At its core, GENIE integrates three collaborative AI agents, each bringing unique strengths to the workflow:
                    </Typography>
                    <br></br>
                    <div style={{marginLeft: 30, marginRight: 30}}>
                        <Typography variant="h6">
                            1. <span style={{ fontWeight: 'bold', textDecoration: 'underline', textDecorationColor: 'red' }}>
                            Jira Miner:
                            </span> Fetches bugs and project insights from Jira, setting the foundation for analysis and resolution.
                        </Typography>
                        <Typography variant="h6">
                            2. <span style={{ fontWeight: 'bold', textDecoration: 'underline', textDecorationColor: 'red' }}>
                            Deep Code:
                            </span> Analyzes codebases to identify vulnerabilities, recommend fixes, and provide actionable insights.
                        </Typography>
                        <Typography variant="h6">
                            3. <span style={{ fontWeight: 'bold', textDecoration: 'underline', textDecorationColor: 'red' }}>
                            TAG (Test Automation Generator):
                            </span> Generates automated tests to detect and validate bugs or verify code changes efficiently.
                        </Typography>
                    </div>
                    <br></br>
                    <Typography variant="h6">
                        These agents work in synergy, with seamless interactions enabling an intelligent flow from bug identification to resolution and validation. By leveraging their combined capabilities, GENIE empowers teams to achieve faster, more accurate debugging, enhanced code quality, and comprehensive test coverage.
                    </Typography>
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                     <img
                     src={AiAgentGraph}
                     alt="AI Agent Graph"
                     style={{ width: '40%', height: 'auto' }}
                     />
                 </div>
            </CardContent>
        </Card>
    //       {/* <div style={{ margin: '50px auto', width: '80%' }}>
    //         <iframe
    //           src="https://docs.google.com/presentation/d/e/2PACX-1vSk0sFE-y0og_QYcTgLP4jjPl51H07UGQb170mFjvKb32A0FMBOUctGykFEFM8RZuNORQpxFv5FK4e-/embed?start=false&loop=false&delayms=3000"
    //           width="100%"
    //           height="480"
    //           allowFullScreen
    //           title="TAG Presentation"
    //         ></iframe>
    //       </div> */}
    );
  }

  export default WelcomeContent;
