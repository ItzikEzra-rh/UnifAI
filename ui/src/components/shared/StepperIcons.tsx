import { StepIconProps, StepLabel, styled } from "@mui/material";

export const CustomStepIcon: React.FC<StepIconProps> = ({ active, completed, icon }) => {
    return (
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          backgroundColor: active || completed ? '#f5504c' : '#e0e0e0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white', 
          fontWeight: 'bold',
          fontSize: '1rem',
        }}
      >
        {icon}
      </div>
    );
  };
  
  export const CustomStepLabel = styled(StepLabel)({
    '& .MuiStepLabel-label': {
      fontSize: '1.25rem',
      color: 'black', 
      fontWeight: 'bold',
    },
  });
  