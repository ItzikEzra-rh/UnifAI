import { StepIconProps, StepLabel, styled } from "@mui/material";

export const CustomStepIcon: React.FC<StepIconProps> = ({ active, completed, icon }) => {
    return (
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          backgroundColor: active || completed ? '#f5504c' : '#e0e0e0', // Red for active/completed, grey otherwise
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white', // Text color
          fontWeight: 'bold',
          fontSize: '1rem', // Adjust font size for the number
        }}
      >
        {icon}
      </div>
    );
  };
  
  // Custom StepLabel styles
  export const CustomStepLabel = styled(StepLabel)({
    '& .MuiStepLabel-label': {
      fontSize: '1.25rem', // Larger font size
      color: 'black', // Black text
      fontWeight: 'bold',
    },
  });
  